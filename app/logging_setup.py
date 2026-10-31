import logging
import re

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
URL_RE = re.compile(r"https?://\S+")


class RedactFilter(logging.Filter):
    """Replaces email addresses and links in log messages."""

    def filter(self, record):
        message = record.getMessage()
        message = EMAIL_RE.sub("[email redacted]", message)
        message = URL_RE.sub("[link redacted]", message)
        record.msg = message
        record.args = ()
        return True


def setup_logging():
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    for handler in root.handlers:
        if not any(isinstance(f, RedactFilter) for f in handler.filters):
            handler.addFilter(RedactFilter())