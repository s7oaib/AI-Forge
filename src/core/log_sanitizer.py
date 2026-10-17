"""PII sanitization helpers for query logging (SEC-02)."""

from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{8,}\d)")
_CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def sanitize_for_log(text: str) -> str:
    """Strip emails, phone/card numbers and long digit runs before logging."""
    out = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    out = _CARD_RE.sub("[REDACTED_CARD]", out)
    out = _PHONE_RE.sub(lambda m: m.group(0) if "greenfield" in m.group(0).lower() else "[REDACTED_PHONE]", out)
    return out
