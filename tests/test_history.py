import sqlite3

import pytest

from app import analyzer, create_app, db, ollama_client
from app.scoring import calculate_score

VALID = {"sender": "Ravi <ravi@gmail.com>", "subject": "Hello", "body": "Meeting at 3pm."}


def fake_analyze(sender, subject, body):
    return {
        "rules": {"findings": [], "rule_score": 0},
        "ai": None,
        "ai_error": "Ollama is off",
        "score": calculate_score(0, None),
    }


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ollama_client,
        "check_status",
        lambda: {"running": True, "model": "llama3.2:3b",
                 "model_available": True, "models": []},
    )
    monkeypatch.setattr(analyzer, "analyze_email", fake_analyze)
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "t.db")})
    return app.test_client()


def test_empty_history_shows_message(client):
    response = client.get("/history")
    assert response.status_code == 200
    assert b"No scans yet" in response.data


def test_scan_is_saved_and_listed(client):
    client.post("/analyze", data=VALID)
    response = client.get("/history")
    assert b"ravi@gmail.com" in response.data


def test_detail_page_loads(client):
    client.post("/analyze", data=VALID)
    response = client.get("/history/1")
    assert response.status_code == 200
    assert b"Risk score" in response.data


def test_unknown_scan_returns_404(client):
    assert client.get("/history/999").status_code == 404


def test_delete_scan(client):
    client.post("/analyze", data=VALID)
    response = client.post("/history/1/delete", follow_redirects=True)
    assert b"Scan deleted" in response.data
    assert b"No scans yet" in response.data


def test_clear_history(client):
    client.post("/analyze", data=VALID)
    client.post("/analyze", data=dict(VALID, subject="Second"))
    response = client.post("/history/clear", follow_redirects=True)
    assert b"All history deleted" in response.data
    assert b"No scans yet" in response.data


def test_search_filters_history(client):
    client.post("/analyze", data=dict(VALID, subject="Invoice overdue"))
    client.post("/analyze", data=dict(VALID, subject="Lunch plans"))
    response = client.get("/history?q=Invoice")
    assert b"Invoice overdue" in response.data
    assert b"Lunch plans" not in response.data


def test_html_in_history_is_escaped(client):
    client.post("/analyze", data=dict(VALID, subject="<b>x</b>"))
    response = client.get("/history")
    assert b"<b>x</b>" not in response.data
    assert b"&lt;b&gt;" in response.data


def test_result_still_shows_when_saving_fails(client, monkeypatch):
    def boom(*args, **kwargs):
        raise sqlite3.OperationalError("disk full")

    monkeypatch.setattr(db, "save_scan", boom)
    response = client.post("/analyze", data=VALID)
    assert response.status_code == 200
    assert b"could not be saved" in response.data


def test_history_page_survives_database_failure(client, monkeypatch):
    def boom(*args, **kwargs):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(db, "list_scans", boom)
    response = client.get("/history")
    assert response.status_code == 200
    assert b"could not be loaded" in response.data