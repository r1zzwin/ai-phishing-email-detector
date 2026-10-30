import pytest

from app import analyzer, create_app, ollama_client
from app.scoring import calculate_score


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ollama_client,
        "check_status",
        lambda: {"running": True, "model": "llama3.2:3b",
                 "model_available": True, "models": []},
    )
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    return app.test_client()

def fake_analyze(sender, subject, body):
    return {
        "rules": {"findings": [], "rule_score": 0},
        "ai": None,
        "ai_error": "Ollama is off",
        "score": calculate_score(0, None),
    }


VALID = {"sender": "Ravi <ravi@gmail.com>", "subject": "Hi", "body": "Meeting at 3pm."}


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Analyze an email" in response.data


def test_missing_fields_are_rejected(client):
    response = client.post("/analyze", data={"sender": "", "subject": "", "body": ""})
    assert response.status_code == 400
    assert b"Sender is required." in response.data


def test_oversized_body_is_rejected(client):
    data = dict(VALID, body="x" * 10001)
    response = client.post("/analyze", data=data)
    assert response.status_code == 400
    assert b"Email body must be" in response.data


def test_valid_email_shows_result_and_warning(client, monkeypatch):
    monkeypatch.setattr(analyzer, "analyze_email", fake_analyze)
    response = client.post("/analyze", data=VALID)
    assert response.status_code == 200
    assert b"Risk score" in response.data
    assert b"Advisory only" in response.data


def test_html_in_input_is_escaped(client, monkeypatch):
    monkeypatch.setattr(analyzer, "analyze_email", fake_analyze)
    data = dict(VALID, subject="<script>alert(1)</script>")
    response = client.post("/analyze", data=data)
    assert b"<script>alert(1)</script>" not in response.data
    assert b"&lt;script&gt;" in response.data