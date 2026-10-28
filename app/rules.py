import re
from email.utils import parseaddr
from urllib.parse import urlparse

MAX_RULE_POINTS = 60

URL_PATTERN = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)
IP_PATTERN = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly"}
SUSPICIOUS_TLDS = (".xyz", ".top", ".click", ".zip", ".work")

URGENT_PHRASES = [
    "act now", "urgent", "immediately", "account suspended",
    "within 24 hours", "final warning", "verify now",
]
CREDENTIAL_PHRASES = [
    "password", "otp", "one-time password", "pin", "cvv",
    "card number", "bank details", "login details", "verify your account",
]
GENERIC_GREETINGS = [
    "dear customer", "dear user", "dear account holder", "dear sir/madam",
]
KNOWN_BRANDS = [
    "paypal", "amazon", "google", "microsoft", "apple",
    "netflix", "sbi", "hdfc", "icici",
]


def _finding(rule_id, name, points, evidence):
    return {"rule": rule_id, "name": name, "points": points, "evidence": evidence}


def _find_phrases(text, phrases):
    text = text.lower()
    return [p for p in phrases if re.search(r"\b" + re.escape(p) + r"\b", text)]


def check_suspicious_links(text):
    for url in URL_PATTERN.findall(text):
        try:
            host = (urlparse(url).hostname or "").lower()
        except ValueError:
            continue
        if IP_PATTERN.match(host):
            return _finding("suspicious_link", "Link points to an IP address", 20, url)
        if host in SHORTENERS:
            return _finding("suspicious_link", "Link uses a URL shortener", 20, url)
        if host.endswith(SUSPICIOUS_TLDS):
            return _finding("suspicious_link", "Link uses a risky domain ending", 20, url)
    return None


def check_urgent_language(text):
    matches = _find_phrases(text, URGENT_PHRASES)
    if matches:
        return _finding("urgent_language", "Urgent or threatening language", 10, ", ".join(matches))
    return None


def check_credential_request(text):
    matches = _find_phrases(text, CREDENTIAL_PHRASES)
    if matches:
        return _finding("credential_request", "Asks for sensitive information", 20, ", ".join(matches))
    return None


def check_sender_mismatch(sender):
    name, address = parseaddr(sender)
    if not address or "@" not in address:
        return None
    domain = address.split("@")[-1].lower()
    for brand in KNOWN_BRANDS:
        if brand in name.lower() and brand not in domain:
            return _finding(
                "sender_mismatch",
                "Display name does not match sender domain",
                20,
                f"Name says '{name}' but domain is '{domain}'",
            )
    return None


def check_generic_greeting(text):
    matches = _find_phrases(text, GENERIC_GREETINGS)
    if matches:
        return _finding("generic_greeting", "Generic greeting", 5, matches[0])
    return None


def analyze_rules(sender, subject, body):
    text = f"{subject}\n{body}"
    candidates = [
        check_suspicious_links(text),
        check_urgent_language(text),
        check_credential_request(text),
        check_sender_mismatch(sender),
        check_generic_greeting(text),
    ]
    findings = [f for f in candidates if f]
    total = sum(f["points"] for f in findings)
    return {"findings": findings, "rule_score": min(total, MAX_RULE_POINTS)}