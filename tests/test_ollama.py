import json

import pytest
import requests

from app import analyzer, ollama_client
from app.ollama_client import OllamaError, validate_ai_output

PHISHING = dict(
    sender="PayPal Support <help@secure-login.xyz>",
    subject="Urgent: account suspended",
    body="Dear customer, verify your password immediately at http://192.168.1.5/login",
)

GOOD_JSON = json.dumps({
    "verdict": "phishing",
    "confidence": 0.92,
    "reasons": ["Asks for a password", "Link goes to an IP address"],
    "evidence": ["verify your password"],
    "next_steps": ["Do not click the link", "Report the email"],
})


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))

    def json(self):
        return self._payload


def raise_connection_error(*args, **kwargs):
    raise requests.ConnectionError("Ollama is off")


def raise_timeout(*args, **kwargs):
    raise requests.Timeout("too slow")


def test_valid_output_is_accepted():
    result = validate_ai_output(GOOD_JSON)
    assert result["verdict"] == "phishing"
    assert result["confidence"] == 0.92
    assert len(result["reasons"]) == 2


def test_invalid_json_is_rejected():
    with pytest.raises(OllamaError):
        validate_ai_output("this is not json")


def test_json_list_instead_of_object_is_rejected():
    with pytest.raises(OllamaError):
        validate_ai_output("[1, 2, 3]")


def test_unknown_verdict_is_rejected():
    with pytest.raises(OllamaError):
        validate_ai_output(json.dumps({"verdict": "banana"}))


def test_confidence_given_as_percentage_is_fixed():
    result = validate_ai_output(json.dumps({"verdict": "suspicious", "confidence": 85}))
    assert result["confidence"] == 0.85


def test_ollama_unavailable_raises_clear_error(monkeypatch):
    monkeypatch.setattr(requests, "post", raise_connection_error)
    with pytest.raises(OllamaError, match="Is it running"):
        ollama_client.analyze_with_ollama("a@b.com", "Hi", "Hello")


def test_ollama_timeout_raises_clear_error(monkeypatch):
    monkeypatch.setattr(requests, "post", raise_timeout)
    with pytest.raises(OllamaError, match="too long"):
        ollama_client.analyze_with_ollama("a@b.com", "Hi", "Hello")


def test_status_when_ollama_is_off(monkeypatch):
    monkeypatch.setattr(requests, "get", raise_connection_error)
    assert ollama_client.check_status()["running"] is False


def test_status_when_ollama_is_running(monkeypatch):
    monkeypatch.setattr(ollama_client, "OLLAMA_MODEL", "llama3.2:3b")
    monkeypatch.setattr(
        requests, "get",
        lambda *a, **k: FakeResponse({"models": [{"name": "llama3.2:3b"}]}),
    )
    status = ollama_client.check_status()
    assert status["running"] is True
    assert status["model_available"] is True


def test_full_flow_with_mocked_ai(monkeypatch):
    monkeypatch.setattr(
        requests, "post", lambda *a, **k: FakeResponse({"response": GOOD_JSON})
    )
    result = analyzer.analyze_email(**PHISHING)
    assert result["ai"]["verdict"] == "phishing"
    assert result["score"]["score"] == 100
    assert result["score"]["category"] == "Critical"


def test_full_flow_when_ollama_is_down(monkeypatch):
    monkeypatch.setattr(requests, "post", raise_connection_error)
    result = analyzer.analyze_email(**PHISHING)
    assert result["ai"] is None
    assert result["ai_error"] is not None
    assert result["score"]["score"] == 60
    assert result["score"]["category"] == "High"