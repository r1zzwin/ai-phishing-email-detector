MAX_RULE_POINTS = 60
MAX_AI_POINTS = 40

AI_VERDICT_POINTS = {"legitimate": 0, "suspicious": 20, "phishing": 40}

CATEGORY_THRESHOLDS = [
    (75, "Critical"),
    (50, "High"),
    (25, "Medium"),
    (0, "Low"),
]


def get_category(score):
    for minimum, label in CATEGORY_THRESHOLDS:
        if score >= minimum:
            return label
    return "Low"


def calculate_score(rule_score, ai_verdict=None):
    rule_points = max(0, min(int(rule_score), MAX_RULE_POINTS))

    verdict = str(ai_verdict).lower().strip() if ai_verdict else None
    ai_used = verdict in AI_VERDICT_POINTS
    ai_points = AI_VERDICT_POINTS[verdict] if ai_used else 0

    score = max(0, min(rule_points + ai_points, 100))

    explanation = f"Rules contributed {rule_points} of {MAX_RULE_POINTS} points. "
    if ai_used:
        explanation += f"AI verdict '{verdict}' contributed {ai_points} of {MAX_AI_POINTS} points."
    else:
        explanation += "AI analysis was not available, so this score uses rules only."

    return {
        "score": score,
        "category": get_category(score),
        "rule_points": rule_points,
        "ai_points": ai_points,
        "ai_used": ai_used,
        "explanation": explanation,
    }