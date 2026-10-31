import logging

import pytest

from app import create_app, ollama_client
from app.logging_setup import RedactFilter
from app.validation import validate_input


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ollama_client, "check_status",
        lambda: {"running": True, "model": "llama3.2:3b",
                 "model_available": True, "models": []},
    )
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "t.db")})
    return app.test_client()


def test_security_headers_are_set(client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


def test_unknown_page_shows_friendly_404(client):
    response = client.get("/nope")
    assert response.status_code == 404
    assert b"Page not found" in response.data


def test_oversized_request_shows_friendly_413(client):
    data = {"sender": "a", "subject": "b", "body": "x" * 70000}
    response = client.post("/analyze", data=data)
    assert response.status_code == 413
    assert b"too large" in response.data


def test_log_filter_hides_emails_and_links():
    record = logging.LogRecord(
        "t", logging.INFO, "f.py", 1, "mail from %s at %s",
        ("ravi@gmail.com", "http://evil.xyz/login"), None,
    )
    RedactFilter().filter(record)
    message = record.getMessage()
    assert "ravi@gmail.com" not in message
    assert "evil.xyz" not in message


def test_newlines_in_sender_and_subject_are_collapsed():
    form = {"sender": "a@b.com\nInjected: line", "subject": "Hi\r\nthere", "body": "text"}
    data, errors = validate_input(form)
    assert errors == []
    assert "\n" not in data["sender"]
    assert data["subject"] == "Hi there"