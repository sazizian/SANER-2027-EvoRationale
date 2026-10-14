"""Best-effort minimization before sending approved repository excerpts to hosted models.

Redaction is NOT a guarantee that confidential source text is safe for external services.
Real use requires organization authorization, a DPA where applicable, and human review.
"""
from __future__ import annotations
import re
from typing import Any

_PATTERNS = (
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
    (re.compile(r"https?://[^\s<>\"']+"), "[URL_REDACTED]"),
    (re.compile(r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*[^\s,;]+"), "[CREDENTIAL_REDACTED]"),
    (re.compile(r"\b(?:ghp_|gho_|github_pat_)[a-zA-Z0-9_]{15,}\b"), "[TOKEN_REDACTED]"),
)


def redact(text: str, max_chars: int = 4096) -> str:
    result = text[:max_chars]
    for pattern, replacement in _PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def minimal_state_view(state: dict[str, Any]) -> dict[str, Any]:
    from .model import ELEMENT_FIELDS
    return {"decision": redact(state["decision"]),
            "elements": [{"id": item["id"], "element_type": field, "text": redact(item["text"]),
                          "keywords": item.get("keywords", [])}
                         for field in ELEMENT_FIELDS for item in state.get(field, [])]}
