"""PII masking for outbound AI prompts."""

from __future__ import annotations

import re
from dataclasses import dataclass

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
NIP_RE = re.compile(r"\b(?:NIP[:\s-]*)?(?:19|20)\d{16}\b", re.IGNORECASE)
LONG_ID_RE = re.compile(r"\b\d{12,20}\b")
VENDOR_RE = re.compile(r"\b(?:PT|CV)\s+[A-Z][A-Za-z0-9&.,\-\s]{2,60}\b")


@dataclass(frozen=True)
class MaskResult:
    text: str
    masked: bool
    counts: dict[str, int]


def mask_pii(text: str) -> MaskResult:
    counts: dict[str, int] = {}

    def sub(label: str, pattern: re.Pattern[str], value: str) -> str:
        def repl(_: re.Match[str]) -> str:
            counts[label] = counts.get(label, 0) + 1
            return f"[MASKED_{label.upper()}]"

        return pattern.sub(repl, value)

    masked = text
    masked = sub("email", EMAIL_RE, masked)
    masked = sub("nip", NIP_RE, masked)
    masked = sub("id", LONG_ID_RE, masked)
    masked = sub("vendor", VENDOR_RE, masked)
    return MaskResult(text=masked, masked=masked != text, counts=counts)
