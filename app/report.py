import json

DISCLAIMER = (
    "Advisory only. This result is not a guarantee. Legitimate emails can be "
    "flagged and phishing emails can be missed."
)

SAFE_STEPS = [
    "Do not click links or open attachments in the email.",
    "Do not reply or share passwords, OTPs or card details.",
    "Contact the sender through an official website or phone number you already trust.",
    "Report the email to your IT team or email provider.",
]


def build_report(scan):
    """Builds the report from a saved scan. The email body is never included."""
    report = scan["report"]
    return {
        "scan_id": scan["id"],
        "created_at_utc": scan["created_at"],
        "sender": scan["sender"],
        "subject": scan["subject"],
        "risk_score": scan["score"],
        "risk_category": scan["category"],
        "ai_verdict": scan["ai_verdict"],
        "explanation": report["explanation"],
        "rule_findings": report["rule_findings"],
        "ai_findings": report["ai"],
        "ai_error": report["ai_error"],
        "safe_next_steps": SAFE_STEPS,
        "disclaimer": DISCLAIMER,
    }


def report_to_json(scan):
    return json.dumps(build_report(scan), indent=2)


def report_to_text(scan):
    data = build_report(scan)
    lines = [
        "PHISHING EMAIL SCAN REPORT",
        "==========================",
        f"Scan ID: {data['scan_id']}",
        f"Time (UTC): {data['created_at_utc']}",
        f"Sender: {data['sender']}",
        f"Subject: {data['subject']}",
        "",
        f"Risk score: {data['risk_score']}/100 ({data['risk_category']})",
        f"AI verdict: {data['ai_verdict'] or 'not available'}",
        f"How the score was calculated: {data['explanation']}",
        "",
        "Rule-based indicators:",
    ]

    if data["rule_findings"]:
        for f in data["rule_findings"]:
            lines.append(f"- {f['name']} (+{f['points']}) | evidence: {f['evidence']}")
    else:
        lines.append("- none found")

    ai = data["ai_findings"]
    if ai:
        lines += ["", "AI findings:"]
        lines.append(f"- Model confidence (the model's own estimate): {round(ai['confidence'] * 100)}%")
        lines += [f"- Reason: {r}" for r in ai["reasons"]]
        lines += [f"- Evidence: {e}" for e in ai["evidence"]]
        lines += [f"- Suggested step: {s}" for s in ai["next_steps"]]
    elif data["ai_error"]:
        lines += ["", f"AI step unavailable: {data['ai_error']}"]

    lines += ["", "Safe next steps:"]
    lines += [f"- {s}" for s in data["safe_next_steps"]]
    lines += ["", data["disclaimer"]]
    return "\n".join(lines) + "\n"