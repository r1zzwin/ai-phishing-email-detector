from app.rules import analyze_rules, MAX_RULE_POINTS

PHISHING = dict(
    sender="PayPal Support <help@secure-login.xyz>",
    subject="Urgent: account suspended",
    body="Dear customer, verify your password immediately at http://192.168.1.5/login",
)


def test_clearly_suspicious_email_hits_all_five_rules():
    result = analyze_rules(**PHISHING)
    assert len(result["findings"]) == 5
    assert result["rule_score"] == 60


def test_rule_total_is_capped():
    result = analyze_rules(**PHISHING)
    raw_total = sum(f["points"] for f in result["findings"])
    assert raw_total == 75
    assert result["rule_score"] == MAX_RULE_POINTS


def test_legitimate_email_scores_zero():
    result = analyze_rules(
        sender="Ravi <ravi@gmail.com>",
        subject="Meeting tomorrow",
        body="Hi, the meeting is at 3pm tomorrow.",
    )
    assert result["findings"] == []
    assert result["rule_score"] == 0


def test_repeated_word_is_counted_only_once():
    result = analyze_rules("Ravi <ravi@gmail.com>", "Hello", "urgent urgent urgent urgent")
    urgent = [f for f in result["findings"] if f["rule"] == "urgent_language"]
    assert len(urgent) == 1
    assert result["rule_score"] == 10


def test_url_shortener_is_flagged():
    result = analyze_rules("Ravi <ravi@gmail.com>", "Link", "See http://bit.ly/abc123")
    assert result["rule_score"] == 20


def test_brand_name_with_wrong_domain_is_flagged():
    result = analyze_rules("Amazon Support <help@random-mail.xyz>", "Hello", "Hi there")
    assert "sender_mismatch" in [f["rule"] for f in result["findings"]]


def test_empty_input_does_not_crash():
    result = analyze_rules("", "", "")
    assert result["rule_score"] == 0