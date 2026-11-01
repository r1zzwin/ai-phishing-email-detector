import pytest

from app import analyzer, create_app, ollama_client
from app.rules import analyze_rules
from app.scoring import calculate_score


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
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "t.db")})
    return app.test_client()


# ---- Ambiguous input ----

def test_ambiguous_email_is_low_on_rules_but_medium_with_ai():
    result = analyze_rules(
        "Ravi <ravi@gmail.com>",
        "Please verify your account",
        "Hi, please verify your account by Friday.",
    )
    assert result["rule_score"] == 20
    assert calculate_score(20, None)["category"] == "Low"
    assert calculate_score(20, "suspicious")["category"] == "Medium"


def test_uppercase_text_is_still_detected():
    result = analyze_rules("Ravi <ravi@gmail.com>", "Hi", "URGENT")
    assert result["rule_score"] == 10


# ---- Malformed input ----

def test_malformed_link_does_not_crash():
    result = analyze_rules("Ravi <ravi@gmail.com>", "Hi", "See http://[broken link")
    assert result["rule_score"] == 0


@pytest.mark.parametrize(
    "sender", ["not an email", "<<<>>>", "@@@", "Ravi <>", "x" * 300]
)
def test_malformed_sender_does_not_crash(sender):
    result = analyze_rules(sender, "Hello", "Hello there")
    assert result["rule_score"] == 0


def test_unicode_and_emoji_do_not_crash():
    result = analyze_rules(
        "Ravi <ravi@gmail.com>", "caf\u00e9 \U0001F600", "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf \U0001F64F"
    )
    assert result["rule_score"] == 0


def test_missing_form_fields_are_rejected(client):
    assert client.post("/analyze", data={}).status_code == 400


def test_whitespace_only_fields_are_rejected(client):
    data = {"sender": "   ", "subject": "   ", "body": "   "}
    response = client.post("/analyze", data=data)
    assert response.status_code == 400
    assert b"Sender is required." in response.data


# ---- Oversized input ----

def test_maximum_length_body_is_handled_by_rules():
    result = analyze_rules("Ravi <ravi@gmail.com>", "Hello", "hello " * 1666)
    assert result["rule_score"] == 0


def test_body_exactly_at_the_limit_is_accepted(client, monkeypatch):
    monkeypatch.setattr(analyzer, "analyze_email", fake_analyze)
    data = {"sender": "Ravi <ravi@gmail.com>", "subject": "Hi", "body": "x" * 10000}
    assert client.post("/analyze", data=data).status_code == 200


def test_overlong_subject_is_rejected(client):
    data = {"sender": "Ravi <ravi@gmail.com>", "subject": "s" * 201, "body": "Hello"}
    response = client.post("/analyze", data=data)
    assert response.status_code == 400
    assert b"Subject must be" in response.data