MAX_SENDER = 254
MAX_SUBJECT = 200
MAX_BODY = 10000


def _clean(value):
    return (value or "").replace("\x00", "").strip()


def validate_input(form):
    data = {
        "sender": _clean(form.get("sender")),
        "subject": _clean(form.get("subject")),
        "body": _clean(form.get("body")),
    }
    errors = []

    if not data["sender"]:
        errors.append("Sender is required.")
    elif len(data["sender"]) > MAX_SENDER:
        errors.append(f"Sender must be {MAX_SENDER} characters or fewer.")

    if not data["subject"]:
        errors.append("Subject is required.")
    elif len(data["subject"]) > MAX_SUBJECT:
        errors.append(f"Subject must be {MAX_SUBJECT} characters or fewer.")

    if not data["body"]:
        errors.append("Email body is required.")
    elif len(data["body"]) > MAX_BODY:
        errors.append(f"Email body must be {MAX_BODY} characters or fewer.")

    return data, errors