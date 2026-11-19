"""Logging that keeps passwords, tokens, and message text out of log files."""

import logging
import re

_SECRET_PATTERNS = (
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)(password|token|secret|api_key)\"?\s*[:=]\s*\"?[^,\s\"]+"),
)


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in _SECRET_PATTERNS:
            message = pattern.sub("[redacted]", message)
        record.msg = message
        record.args = ()
        return True


def configure_logging(level: str) -> logging.Logger:
    logger = logging.getLogger("safevillage")
    logger.setLevel(level.upper())
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    handler.addFilter(RedactionFilter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger
