"""Mechanical screens for substantive local proof, never relation classifiers.

Whitespace, Markdown code-span delimiters and terminal prose commas/periods do
not make a new documentary assertion. Internal punctuation and operators are
preserved. This conservative screen cannot establish target entailment or
architectural materiality; those remain explicitly model-assessed.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from .diff_context import DIFF_SOURCE_TYPES, _lines


def _normalise(text: str, *, diff_prefix: bool = True) -> str:
    if diff_prefix and text[:1] in {"+", "-", " "}:
        text = text[1:]
    text = text.strip()
    literal_pattern = r'''("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')'''
    parts = re.split(literal_pattern, text)
    text = "".join(part if index % 2 else part.replace("`", "")
                   for index, part in enumerate(parts))
    # Terminal prose punctuation is formatting; code operators, numeric
    # endpoints and tuple punctuation keep their literal distinctions.
    if (re.search(r"[A-Za-z_][.,]+$", text)
            and not re.search(r"[<>=!&|{}\[\]();]", text)):
        text = text.rstrip(".,")
    # Preserve spaces inside quoted literals. Whitespace outside literals and
    # Markdown code-span delimiters is ignored only for this conservative screen.
    parts = re.split(literal_pattern, text)
    return "".join(part if index % 2 else re.sub(r"\s+", "", part.replace("`", ""))
                   for index, part in enumerate(parts))


@lru_cache(maxsize=64)
def _canonical_alignment(source_type: str, content: str):
    """Map exact surviving assertions without quadratic character alignment.

    Full earlier normalized line assertions must match current text. Merging
    their intervals handles reflow in either direction. An exceptional source
    exceeding the match-work bound is conservatively ineligible as fresh proof.
    """
    rows = _lines({"source_type": source_type, "content": content}) or []
    old_assertions, new_parts, added_ranges = set(), [], {}
    new_offset = 0
    for start, _, role, text in rows:
        normal = _normalise(text)
        if role in {"removed", "unchanged"}:
            if normal:
                old_assertions.add(normal)
        if role in {"added", "unchanged"}:
            new_parts.append(normal)
            if role == "added" and normal:
                added_ranges[start] = (new_offset, new_offset + len(normal))
            new_offset += len(normal)
    new = "".join(new_parts)
    matches, work = [], 0
    for assertion in sorted(old_assertions, key=len, reverse=True):
        start = new.find(assertion)
        while start >= 0:
            work += 1
            if work > 200_000:
                return added_ranges, None
            matches.append((start, start + len(assertion)))
            start = new.find(assertion, start + 1)
    merged = []
    for left, right in sorted(matches):
        if merged and left <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], right))
        else:
            merged.append((left, right))
    return added_ranges, tuple(merged)


def _is_reflowed_assertion(artifact: dict[str, Any], line: dict[str, Any]) -> bool:
    added_ranges, retained_ranges = _canonical_alignment(artifact["source_type"], artifact["content"])
    position = added_ranges.get(line["start"])
    if position is None:
        return False
    if retained_ranges is None:
        return True  # Exceptional matching workload: abstain on fresh support.
    left, right = position
    return any(start <= left and right <= end for start, end in retained_ranges)


def substantive_changed_proof(artifact: dict[str, Any], before_lines: list[dict[str, Any]],
                              after_lines: list[dict[str, Any]]) -> bool:
    """Require meaningful whole-source and selected-proof differences.

    Proofs are previously bound to canonical source lines. The source-level
    check prevents omitted old proof handles from rescuing a formatting-only
    edit. Selected proof still has to carry a difference of its own.
    """
    if artifact["source_type"] not in DIFF_SOURCE_TYPES:
        return any(_normalise(line["text"], diff_prefix=False) for line in after_lines)
    rows = _lines(artifact)
    if rows is None:
        return False
    old = "".join(_normalise(text) for _, _, role, text in rows
                  if role in {"removed", "unchanged"})
    new = "".join(_normalise(text) for _, _, role, text in rows
                  if role in {"added", "unchanged"})
    if old == new:
        return False
    before = "".join(_normalise(line["text"]) for line in before_lines
                     if line["role"] == "removed")
    after = "".join(_normalise(line["text"]) for line in after_lines
                    if line["role"] == "added")
    return bool(before or after) and before != after


def substantive_current_added_proof(artifact: dict[str, Any], line: dict[str, Any]) -> bool:
    """Reject formatting/reflow of a prior assertion as fresh local support.

    Ordinary current documents use statement lines. Diff evidence must use an
    added assertion that is not a whitespace/formatting copy of earlier source.
    Repetition alone does not supply a substantive new local contribution.
    """
    if artifact["source_type"] not in DIFF_SOURCE_TYPES:
        return line["role"] == "statement" and bool(_normalise(line["text"], diff_prefix=False))
    if line["role"] != "added":
        return False
    value = _normalise(line["text"])
    rows = _lines(artifact)
    if not value or rows is None:
        return False
    old = {_normalise(text) for _, _, role, text in rows
           if role in {"removed", "unchanged"}}
    return value not in old and not _is_reflowed_assertion(artifact, line)


def substantive_current_added_proofs(artifact: dict[str, Any], lines: list[dict[str, Any]]) -> bool:
    """Screen compound current proof against whole earlier assertion spans.

    A sentence reflowed into two lines is still the same documentary assertion,
    including when another part of the hunk changed. Compare complete contiguous
    earlier line spans instead of substring prefixes, so meaningful trailing
    operators, tuple commas and numeric punctuation are preserved.
    """
    if artifact["source_type"] not in DIFF_SOURCE_TYPES:
        return any(substantive_current_added_proof(artifact, line) for line in lines)
    current = [line for line in lines if line["role"] == "added"]
    if not current or not any(substantive_current_added_proof(artifact, line) for line in current):
        return False
    assertion = "".join(_normalise(line["text"]) for line in current)
    rows = _lines(artifact)
    if not assertion or rows is None:
        return False
    earlier = [_normalise(text) for _, _, role, text in rows
               if role in {"removed", "unchanged"} and _normalise(text)]
    for start in range(len(earlier)):
        span = ""
        for part in earlier[start:]:
            span += part
            if span == assertion:
                return False
            if len(span) >= len(assertion):
                break
    return True
