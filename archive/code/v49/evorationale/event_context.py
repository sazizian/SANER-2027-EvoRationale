"""Bounded, canonical same-event context and exhaustive exact diff passages.

This module selects source data, never relations. An event is joined only by
explicit commit, repository, file and capture identity. Inferred hunk prefixes,
titles and human labels are deliberately not part of the grouping contract.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .diff_context import DIFF_SOURCE_TYPES, canonical_diff_context
from .evidence_semantics import evidence_spans
from .model import artifact_digest, artifact_key, eligible, elements, tokenize
from .redaction import _PATTERNS, redact

DEFAULT_EVENT_SOURCE_BYTES = 48000
_FULL_COMMIT = re.compile(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})\Z")
_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")
_DERIVED_TEXT_BUDGET = 0


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def redact_event_source(text: str) -> str:
    """Screen full source spans while preserving its numbered line boundaries.

    Redacting a credential expression spanning multiple lines must screen the
    continuation AND keep later source-owned citation line ranges stable.
    Replacement markers are outbound context only, never exact quotations.
    """
    screened = text
    for pattern, replacement in _PATTERNS:
        def replace(match: re.Match[str]) -> str:
            breaks = "".join(re.findall(r"\r\n|[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]", match.group(0)))
            return replacement + breaks
        screened = pattern.sub(replace, screened)
    return screened


def _identity(artifact: dict[str, Any]) -> dict[str, Any]:
    commit = artifact.get("source_commit_sha", "")
    source_file = artifact.get("source_file", "")
    pinned = (isinstance(commit, str) and bool(_FULL_COMMIT.fullmatch(commit))
              and isinstance(source_file, str) and bool(source_file.strip()))
    return {"repository": artifact["repository"],
            "source_commit_sha": commit.lower() if pinned else "",
            "source_file": source_file if pinned else "",
            "first_auditable_at": artifact["first_auditable_at"],
            "pinned": pinned}


def _group_key(artifact: dict[str, Any]) -> tuple[str, ...]:
    identity = _identity(artifact)
    if not identity["pinned"]:
        return ("singleton", artifact_key(artifact))
    return ("pinned", identity["repository"], identity["source_commit_sha"],
            identity["source_file"], identity["first_auditable_at"])


def _bound(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def _canonical(artifact: dict[str, Any]) -> None:
    if artifact_digest(artifact) != artifact.get("content_sha256"):
        raise ValueError(f"event_context_canonical_digest_mismatch:{artifact_key(artifact)}")


def _hunk_count(artifact: dict[str, Any]) -> int:
    if artifact.get("source_type") in DIFF_SOURCE_TYPES:
        return max(1, sum(bool(_HEADER.match(line))
                          for line in artifact["content"].splitlines()))
    return 1


def select_event_batches(state: dict[str, Any], history: list[dict[str, Any]],
                         max_reads: int, max_chars: int = DEFAULT_EVENT_SOURCE_BYTES,
                         max_hunks: int = 18) -> list[list[dict[str, Any]]]:
    """Select eligible canonical artifacts without starving noncentral S0 items.

    ``max_chars`` is a UTF-8 source-byte bound, which is stricter than a character
    bound. Oversized individual artifacts are omitted rather than truncated.
    Read/hunk/context limits may split a pinned event. Such batches explicitly
    report event_group_complete=False; no omitted sibling is silently implied.
    """
    for name, value in (("max_reads", max_reads), ("max_chars", max_chars),
                        ("max_hunks", max_hunks)):
        _bound(name, value)
    if not max_reads or not max_chars or not max_hunks:
        return []
    canonical: dict[str, dict[str, Any]] = {}
    for artifact in history:
        _canonical(artifact)
        key = artifact_key(artifact)
        if key in canonical and canonical[key] != artifact:
            raise ValueError(f"event_context_conflicting_artifact:{key}")
        if eligible(state, artifact):
            canonical[key] = artifact
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for artifact in canonical.values():
        groups.setdefault(_group_key(artifact), []).append(artifact)
    targets = [tokenize(item["text"] + " " + " ".join(item.get("keywords", [])))
               for item in elements(state)]

    def priority(group: list[dict[str, Any]]) -> tuple[int, float, tuple[str, ...]]:
        contexts = [canonical_diff_context(a, max_chars=max_chars) for a in group]
        tier = (0 if any(c and c["complete"] for c in contexts)
                else 1 if any(a.get("source_type") not in DIFF_SOURCE_TYPES for a in group)
                else 2)
        tokens = [tokenize(a["title"] + "\n" + a["content"])
                  for a in group]
        # All S0 elements contribute; central flags never gate source access.
        relevance = sum(max((len(t & terms) / max(1, len(terms)) for t in tokens),
                            default=0.0) for terms in targets)
        return tier, -relevance, _group_key(group[0])

    batches: list[list[dict[str, Any]]] = []
    reads = 0
    for group in sorted(groups.values(), key=priority):
        ordered = sorted(group, key=artifact_key)
        all_keys = [artifact_key(a) for a in ordered]
        chunks: list[list[dict[str, Any]]] = []
        current: list[dict[str, Any]] = []
        used_bytes = used_hunks = 0
        for artifact in ordered:
            if reads >= max_reads:
                break
            source_bytes = len(artifact["content"].encode("utf-8"))
            hunk_count = _hunk_count(artifact)
            if source_bytes > max_chars or hunk_count > max_hunks:
                continue
            if current and (used_bytes + source_bytes > max_chars
                            or used_hunks + hunk_count > max_hunks):
                chunks.append(current)
                current, used_bytes, used_hunks = [], 0, 0
            current.append(artifact)
            used_bytes += source_bytes
            used_hunks += hunk_count
            reads += 1
        if current:
            chunks.append(current)
        for chunk in chunks:
            complete = len(chunk) == len(ordered)
            batches.append([{**a, "_event_batch_complete": complete,
                             "_event_group_artifact_keys": all_keys,
                             "_event_source_byte_bound": max_chars}
                            for a in chunk])
        if reads >= max_reads:
            break
    return batches


def event_context_view(batch: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a redacted outbound view, preserving canonical hashes separately.

    Views retain full raw diffs and represent duplicate before/after strings
    with hashes and an explicit deterministic derivation instruction.
    ``complete`` requires both individual parsed diffs and full event coverage.
    A complete captured event is not a claim that the entire repository commit
    was captured. Direct pinned batches without selector annotations cannot
    attest that all captured siblings were included.
    """
    if not batch:
        raise ValueError("event_context_empty_batch")
    keys = [artifact_key(a) for a in batch]
    if len(keys) != len(set(keys)):
        raise ValueError("event_context_duplicate_artifact")
    group_keys = {_group_key(a) for a in batch}
    if len(group_keys) != 1:
        raise ValueError("event_context_cross_identity_batch")
    for artifact in batch:
        _canonical(artifact)
    identity = _identity(batch[0])
    canonical_identity = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    outbound_identity = {k: redact(v, max_chars=len(v)) if isinstance(v, str) else v
                         for k, v in identity.items()}
    expected_keys = batch[0].get("_event_group_artifact_keys")
    annotations_match = (isinstance(expected_keys, list)
                         and all(a.get("_event_group_artifact_keys") == expected_keys
                                 and a.get("_event_batch_complete") is True for a in batch)
                         and set(keys) == set(expected_keys))
    group_complete = annotations_match or (not identity["pinned"] and len(batch) == 1)
    source_bytes = sum(len(a["content"].encode("utf-8")) for a in batch)
    selected_bounds = [a.get("_event_source_byte_bound", DEFAULT_EVENT_SOURCE_BYTES)
                       for a in batch]
    for bound in selected_bounds:
        _bound("event_source_byte_bound", bound)
    if source_bytes > min(selected_bounds):
        raise ValueError("event_context_source_bytes_exceed_bound")
    result: dict[str, Any] = {
        "context_kind": "CANONICAL_CAPTURED_SAME_EVENT_FILE_CONTEXT",
        "artifact_keys": keys, "artifact_ids": [a["artifact_id"] for a in batch],
        "identity": outbound_identity, "identity_sha256": _sha(canonical_identity),
        "event_group_complete": group_complete, "complete": group_complete,
        "source_bytes": source_bytes, "redacted": outbound_identity != identity,
        "canonical_artifacts": [],
        "coverage_limit": "Only canonical captured artifacts; not a complete repository commit.",
    }
    derived_remaining = _DERIVED_TEXT_BUDGET
    for artifact in batch:
        content = artifact["content"]
        screened = redact_event_source(content)
        result["redacted"] |= screened != content
        entry: dict[str, Any] = {
            "artifact_key": artifact_key(artifact), "artifact_id": artifact["artifact_id"],
            "content_sha256": artifact["content_sha256"],
            "source_type": artifact["source_type"], "raw_source_sha256": _sha(content),
            "source_location": redact(artifact["source_location"],
                                      max_chars=len(artifact["source_location"])),
        }
        context = canonical_diff_context(artifact, max_chars=len(content))
        if artifact.get("source_type") in DIFF_SOURCE_TYPES:
            entry["raw_diff"] = screened
            entry["diff_complete"] = bool(context and context["complete"])
            result["complete"] &= entry["diff_complete"]
            if not entry["diff_complete"]:
                entry["diff_incomplete_reason"] = (context or {}).get(
                    "incomplete_reason", "unrecognized_unified_diff")
            else:
                derived_size = sum(len(h["before_text"]) + len(h["after_text"])
                                   for h in context["hunks"])
                result["redacted"] |= context["redacted"]
                if derived_size <= derived_remaining:
                    entry["hunks"] = [{k: h[k] for k in ("header", "before_text", "after_text")}
                                      for h in context["hunks"]]
                    derived_remaining -= derived_size
                else:
                    entry["hunks"] = [{"header": h["header"],
                                       "before_text_sha256": _sha(h["before_text"]),
                                       "after_text_sha256": _sha(h["after_text"])}
                                      for h in context["hunks"]]
                    entry["before_after_derivation"] = (
                        "For each raw_diff @@ hunk: before includes unchanged and '-' lines; "
                        "after includes unchanged and '+' lines; remove exactly one role prefix. "
                        "Headers/metadata/annotations are excluded. Duplicate text omitted to bound payload.")
        else:
            entry["text"] = screened
        result["canonical_artifacts"].append(entry)
    return result


def exact_event_passages(artifact: dict[str, Any], max_chars: int = 650) -> list[str]:
    """Exact contiguous windows covering every changed line in a valid diff.

    There is no lexical top-k filter. A changed line longer than the quotation
    bound raises a clear error instead of silently dropping its evidence. Prose
    uses the existing exact-span extractor and has no changed-line guarantee.
    This local function never redacts source quotations; outbound views do.
    """
    _bound("max_chars", max_chars)
    if not max_chars:
        raise ValueError("exact_event_passage_bound_must_be_positive")
    _canonical(artifact)
    content = artifact["content"]
    if artifact.get("source_type") not in DIFF_SOURCE_TYPES:
        return evidence_spans(content, max_chars=max_chars)
    context = canonical_diff_context(artifact, max_chars=len(content))
    if not context or not context["complete"]:
        reason = (context or {}).get("incomplete_reason", "unrecognized_unified_diff")
        raise ValueError(f"exact_event_passages_incomplete_diff:{reason}")
    lines = content.splitlines(keepends=True)
    offsets = []
    cursor = 0
    active = False
    changed = []
    for index, line in enumerate(lines):
        offsets.append(cursor)
        cursor += len(line)
        if _HEADER.match(line):
            active = True
        elif active and line.startswith(("+", "-")):
            if len(line.rstrip("\r\n")) > max_chars:
                raise ValueError(f"exact_event_passage_changed_line_exceeds_bound:{index + 1}")
            changed.append(index)
    passages: list[str] = []
    covered_until = -1
    for index in changed:
        if index <= covered_until:
            continue
        start = index
        if (index and not _HEADER.match(lines[index - 1])
                and len(lines[index - 1]) + len(lines[index].rstrip("\r\n")) <= max_chars):
            start = index - 1
        end = index
        while end + 1 < len(lines) and not _HEADER.match(lines[end + 1]):
            candidate = content[offsets[start]:offsets[end + 1] + len(lines[end + 1])].rstrip("\r\n")
            if len(candidate) > max_chars:
                break
            end += 1
        passage = content[offsets[start]:offsets[end] + len(lines[end])].rstrip("\r\n")
        if len(passage) > max_chars:
            # A line of exactly max_chars plus its newline is represented without newline.
            passage = lines[index].rstrip("\r\n")
            end = index
        passages.append(passage)
        covered_until = end
    return list(dict.fromkeys(passages))


def quotable_event_passages(artifact: dict[str, Any], max_chars: int = 650
                           ) -> tuple[list[str], int]:
    """Recover safe exact spans without hiding an entire sensitive window.

    A sensitive neighboring line must not remove unrelated changed lines from
    the citation catalog. Split that window at sensitive lines, retaining only
    contiguous ORIGINAL source bytes. Diff fallbacks contain a changed line;
    unchanged context alone is never manufactured into a new citation. The
    omitted count describes full windows excluded, including recovered ones.
    """
    quotes: list[str] = []
    omitted = 0
    is_diff = artifact.get("source_type") in DIFF_SOURCE_TYPES
    content = artifact["content"]
    source_sensitive = [(m.start(), m.end()) for pattern, _ in _PATTERNS
                        for m in pattern.finditer(content)]
    for quote in exact_event_passages(artifact, max_chars=max_chars):
        # A quotation can begin halfway through a multiline source match.
        # Screen all original occurrences before sending that exact text;
        # local window matching alone would miss a credential continuation.
        sensitive = []
        occurrence = content.find(quote)
        while occurrence >= 0:
            end = occurrence + len(quote)
            sensitive.extend((max(left, occurrence) - occurrence, min(right, end) - occurrence)
                             for left, right in source_sensitive
                             if left < end and right > occurrence)
            occurrence = content.find(quote, occurrence + 1)
        sensitive.extend((m.start(), m.end()) for pattern, _ in _PATTERNS
                         for m in pattern.finditer(quote))
        if not sensitive and redact(quote, max_chars=len(quote)) == quote:
            quotes.append(quote)
            continue
        omitted += 1
        run: list[str] = []
        # Match against the entire window: credential patterns can span a
        # newline, so screening each line independently could disclose its
        # continuation. Suppress every ORIGINAL line touched by such a match.

        def retain() -> None:
            fallback = "".join(run).rstrip("\r\n")
            if (fallback and redact(fallback, max_chars=len(fallback)) == fallback
                    and (not is_diff or any(line.startswith(("+", "-")) for line in run))):
                quotes.append(fallback)
            run.clear()

        offset = 0
        for line in quote.splitlines(keepends=True):
            end = offset + len(line)
            if any(left < end and right > offset for left, right in sensitive):
                retain()
            else:
                run.append(line)
            offset = end
        retain()
    return list(dict.fromkeys(quotes)), omitted


def semantic_context_view(context: dict[str, Any]) -> dict[str, Any]:
    """Minimize redundant audit metadata, keeping every source byte and boundary.

    Full version keys and before/after hashes remain in the code-owned canonical
    view and final assessment. The model sees one canonical content hash per
    source; repeating multiple opaque hashes does not add semantic evidence.
    """
    keys = ("context_kind", "identity", "identity_sha256", "event_group_complete",
            "complete", "redacted", "coverage_limit")
    result = {k: context[k] for k in keys}
    fields = {"artifact_id", "content_sha256", "source_type", "raw_diff", "text",
              "diff_complete", "diff_incomplete_reason"}
    result["canonical_artifacts"] = [{k: v for k, v in a.items() if k in fields}
                                     for a in context["canonical_artifacts"]]
    result["before_after_derivation"] = (
        "Per raw diff hunk: before is unchanged plus removed lines; after is unchanged "
        "plus added lines. Remove one role prefix; exclude headers and annotations.")
    return result
