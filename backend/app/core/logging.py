import logging
import re
import sys

_SENSITIVE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Redact passwords in credentialed URLs (e.g., postgresql://user:pass@host)
    (re.compile(r"(://[^:/@\s]+:)([^@\s]+)(@)"), r"\1***\3"),
    # Redact Bearer tokens
    (re.compile(r"(?i)(Bearer\s+)([A-Za-z0-9._\-+/=]+)"), r"\1***"),
    # Redact common API key prefixes (OpenAI, Anthropic, GitHub, Google)
    (re.compile(r"\b(sk-(?:proj-|ant-)?[A-Za-z0-9_\-]{12,}|AIza[0-9A-Za-z_\-]{20,})\b"), "***"),
)


def redact_sensitive_text(message: str) -> str:
    """Mask credentialed URLs, bearer tokens, and API key patterns in log text."""
    redacted = message
    for pattern, replacement in _SENSITIVE_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


class SecretRedactingFilter(logging.Filter):
    """Logging filter preventing accidental credential or API key leakage."""

    def filter(self, record: logging.LogRecord) -> bool:
        rendered = record.getMessage()
        sanitized = redact_sensitive_text(rendered)
        if sanitized != rendered:
            record.msg = sanitized
            record.args = ()
        return True


def configure_logging(level: str = "INFO") -> None:
    """Configure consistent structured-style logging with secret redaction."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
        force=True,
    )
    redactor = SecretRedactingFilter()
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(redactor)
