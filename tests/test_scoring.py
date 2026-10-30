import pytest
from app.scoring import calculate_score, get_category


@pytest.mark.parametrize(
    "score, expected",
    [
        (0, "Low"), (24, "Low"),
        (25, "Medium"), (49, "Medium"),
        (50, "High"), (74, "High"),
        (75, "Critical"), (100, "Critical"),
    ],
)
def test_category_thresholds(score, expected):
    assert get_category(score) == expected


def test_worked_example_rules_plus_ai():
    result = calculate_score(rule_score=20, ai_verdict="suspicious")
    assert result["score"] == 40
    assert result["category"] == "Medium"


def test_maximum_score_is_100():
    result = calculate_score(rule_score=60, ai_verdict="phishing")
    assert result["score"] == 100
    assert result["category"] == "Critical"


def test_rule_points_are_capped_at_60():
    result = calculate_score(rule_score=999, ai_verdict=None)
    assert result["rule_points"] == 60


def test_works_when_ai_is_unavailable():
    result = calculate_score(rule_score=30, ai_verdict=None)
    assert result["ai_used"] is False
    assert result["score"] == 30


def test_invalid_ai_verdict_is_ignored():
    result = calculate_score(rule_score=30, ai_verdict="banana")
    assert result["ai_used"] is False
    assert result["score"] == 30