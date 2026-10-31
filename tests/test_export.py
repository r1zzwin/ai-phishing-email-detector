import json

import pytest

from app import analyzer, create_app, ollama_client
from app.report import report_to_json, report_to_text
from app.scoring import calculate_score

SCAN = {
    "id": 7,
    "created_at": "2026-10-31T10:00:00+00:00",
    "sender": "PayPal Support <help@secure-login.xyz>",
    "subject": "Urgent",
    "score": 80,
    "category": "Critical",
    "ai_verdict": "phishing",
    "report": {
        "rule_findings": [{"rule": "urgent_language",
                           "name": "Urgent or threatening language",
                           "points": 10, "evidence": "urgent"}],
        "rule_points": 10,
        "ai": {"verdict": "phishing", "confidence": 0.9,
               "reasons": ["Asks for a password"],
               "evidence": ["verify your password"],
               "next_steps": ["Do not click the link"]},
        "ai_error": None,
        "explanation": "Rules contributed 10 of 60 points.",
    },
}

VALID = {"sender": "Ravi <ravi@gmail.com>", "subject": "Hello", "body": "SECRETBODYTEXT"}


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
        ollama_client, "check_status",
        lambda: {"running": True, "model": "llama3.2:3b",
                 "model_available": True, "models": []},
    )
    monkeypatch.setattr(analyzer, "analyze_email", fake_analyze)
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "t.db")})
    return app.test_client()


def test_text_report_contains_key_information():
    text = report_to_text(SCAN)
    assert "Risk score: 80/100 (Critical)" in text
    assert "Urgent or threatening language" in text
    assert "Advisory only" in text


def test_json_report_is_valid_and_has_no_body_field():
    data = json.loads(report_to_json(SCAN))
    assert data["risk_score"] == 80
    assert "body" not in data


def test_text_report_when_ai_was_unavailable():
    scan = json.loads(json.dumps(SCAN))
    scan["report"]["ai"] = None
    scan["report"]["ai_error"] = "Ollama is off"
    scan["ai_verdict"] = None
    text = report_to_text(scan)
    assert "AI step unavailable: Ollama is off" in text
    assert "AI verdict: not available" in text


def test_download_text_report(client):
    client.post("/analyze", data=VALID)
    response = client.get("/history/1/export/txt")
    assert response.status_code == 200
    assert response.mimetype == "text/plain"
    assert "attachment" in response.headers["Content-Disposition"]
    assert b"PHISHING EMAIL SCAN REPORT" in response.data


def test_download_json_report(client):
    client.post("/analyze", data=VALID)
    response = client.get("/history/1/export/json")
    assert response.status_code == 200
    assert json.loads(response.data)["risk_category"] == "Low"


def test_email_body_is_not_in_any_export(client):
    client.post("/analyze", data=VALID)
    assert b"SECRETBODYTEXT" not in client.get("/history/1/export/txt").data
    assert b"SECRETBODYTEXT" not in client.get("/history/1/export/json").data


def test_unknown_format_returns_404(client):
    client.post("/analyze", data=VALID)
    assert client.get("/history/1/export/pdf").status_code == 404


def test_export_of_missing_scan_returns_404(client):
    assert client.get("/history/999/export/txt").status_code == 404