"""Code-owned before/after context for canonical captured unified diffs.

Exact quotations retain their original +/- prefixes and source bytes. Derived
views are separately labeled, bounded, redacted, and tied to the canonical
artifact hash. This parser does not classify architectural relations.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from .redaction import redact

DIFF_SOURCE_TYPES = {
    "git_commit_diff_hunk", "git_commit_diff", "pull_request_diff_excerpt",
    "pull_request_diff_hunk",
}
MAX_DIFF_CONTEXT_CHARS = 6000
_HEADER = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")


def _lines(artifact: dict[str, Any]) -> list[tuple[int, int, str, str]] | None:
    content = artifact.get("content", "")
    if artifact.get("source_type") not in DIFF_SOURCE_TYPES or not isinstance(content, str):
        return None
    source_lines = content.splitlines(keepends=True)
    if not any(_HEADER.match(line) for line in source_lines):
        return None
    records = []
    active = False
    offset = 0
    for line in source_lines:
        if _HEADER.match(line):
            role = "header"
            active = True
        elif not active:
            role = "metadata"
        elif line.startswith("\\ No newline at end of file"):
            role = "annotation"
        elif line.startswith("+"):
            role = "added"
        elif line.startswith("-"):
            role = "removed"
        elif line.startswith(" ") or not line.strip():
            role = "unchanged"
        else:
            role = "unparsed"
        records.append((offset, offset + len(line), role, line))
        offset += len(line)
    return records


def quote_line_roles(artifact: dict[str, Any], quote: str) -> list[str]:
    """Union roles of every exact occurrence; ambiguous occurrences fail open
    only to semantic review, never become deterministic positive evidence.
    """
    records = _lines(artifact)
    if records is None or not isinstance(quote, str) or not quote:
        return []
    content = artifact["content"]
    roles = set()
    start = content.find(quote)
    while start >= 0:
        end = start + len(quote)
        roles.update(role for left, right, role, line in records
                     if left < end and right > start and line.strip())
        start = content.find(quote, start + 1)
    return sorted(roles)


def removed_only_quote(artifact: dict[str, Any], quote: str) -> bool:
    return quote_line_roles(artifact, quote) == ["removed"]


def canonical_diff_context(artifact: dict[str, Any], *,
                           max_chars: int = MAX_DIFF_CONTEXT_CHARS) -> dict[str, Any] | None:
    records = _lines(artifact)
    if records is None:
        return None
    content = artifact["content"]
    result: dict[str, Any] = {
        "source_type": artifact["source_type"],
        "canonical_content_sha256": artifact.get("content_sha256", ""),
        "raw_diff_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "context_kind": "MECHANICALLY_DERIVED_FROM_CANONICAL_UNIFIED_DIFF",
        "complete": False,
        "redacted": False,
        "hunks": [],
    }
    if len(content) > max_chars:
        result["incomplete_reason"] = "diff_context_exceeds_bound"
        return result
    if any(role == "unparsed" for _, _, role, _ in records):
        result["incomplete_reason"] = "unparsed_diff_line"
        return result
    current: dict[str, Any] | None = None
    for _, _, role, line in records:
        if role == "header":
            # The trailing header description is old contextual text, not a
            # declaration in either reconstructed side.
            match = _HEADER.match(line)
            current = {"header": line.strip(), "before_text": "", "after_text": "",
                       "declared_before_lines": int(match.group(1) or "1"),
                       "declared_after_lines": int(match.group(2) or "1"),
                       "observed_before_lines": 0, "observed_after_lines": 0}
            result["hunks"].append(current)
        elif current is not None and role in {"added", "removed", "unchanged"}:
            text = line[1:] if line[:1] in {"+", "-", " "} else line
            if role in {"removed", "unchanged"}:
                current["before_text"] += text
                current["observed_before_lines"] += 1
            if role in {"added", "unchanged"}:
                current["after_text"] += text
                current["observed_after_lines"] += 1
    if any(hunk["declared_before_lines"] != hunk["observed_before_lines"]
           or hunk["declared_after_lines"] != hunk["observed_after_lines"]
           for hunk in result["hunks"]):
        result["hunks"] = []
        result["incomplete_reason"] = "diff_hunk_line_counts_mismatch"
        return result
    for hunk in result["hunks"]:
        for key in ("header", "before_text", "after_text"):
            original = hunk[key]
            screened = redact(original, max_chars=max_chars)
            result["redacted"] |= screened != original
            hunk[key] = screened
    result["complete"] = True
    return result
