import logging
import re
import sys
from typing import Any


# Patterns to redact from logs
SENSITIVE_PATTERNS = [
    re.compile(r'(api[-_]?key["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'(password["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'(authorization["\']?\s*[:=]\s*["\']?Bearer\s+)([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'(secret[-_]?key["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE),
]


class SensitiveDataFilter(logging.Filter):
    """Filter that masks sensitive tokens, passwords, and API keys from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.mask_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.mask_value(v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.mask_value(v) for v in record.args)
        return True

    @staticmethod
    def mask_text(text: str) -> str:
        for pattern in SENSITIVE_PATTERNS:
            text = pattern.sub(r"\1[REDACTED]", text)
        return text

    @classmethod
    def mask_value(cls, val: Any) -> Any:
        if isinstance(val, str):
            return cls.mask_text(val)
        return val


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configures application-wide logging with security redactors."""
    logger = logging.getLogger("knowledge_ai")
    logger.setLevel(level)

    # Avoid adding duplicate handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()
