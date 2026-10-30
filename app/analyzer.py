from . import ollama_client
from .rules import analyze_rules
from .scoring import calculate_score


def analyze_email(sender, subject, body):
    rules = analyze_rules(sender, subject, body)

    ai, ai_error = None, None
    try:
        ai = ollama_client.analyze_with_ollama(sender, subject, body)
    except ollama_client.OllamaError as error:
        ai_error = str(error)

    score = calculate_score(
        rules["rule_score"], ai["verdict"] if ai else None
    )
    return {"rules": rules, "ai": ai, "ai_error": ai_error, "score": score}