"""Strict, version-aware input boundaries. Evidence is NEVER a model-generated authority.

Public JSON dictionaries are retained for interoperability with GitHub exports and replay
snapshots; these functions validate and canonicalize them at the trust boundary.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any

ELEMENT_FIELDS = (
    "goals", "requirements", "assumptions", "original_evidence", "quality_attributes",
    "constraints_dependencies", "implementation_scope",
)
DRIFT_TYPES = {
    "assumptions": "assumption_drift", "original_evidence": "evidence_drift",
    "requirements": "requirement_drift", "implementation_scope": "implementation_drift",
    "quality_attributes": "quality_attribute_drift",
    "constraints_dependencies": "dependency_drift",
}
RELATIONS = {"supports", "weakens", "contradicts", "supersedes"}
OUTCOMES = {"KEEP", "REVALIDATE", "REVISE", "REOPEN"}


class ValidationError(ValueError):
    pass


def parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("Timestamp must be a nonempty ISO-8601 string")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"Invalid timestamp: {value}") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValidationError(f"Timestamp must include timezone: {value}")
    return dt.astimezone(timezone.utc)


def iso(value: str) -> str:
    return parse_timestamp(value).isoformat().replace("+00:00", "Z")


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def artifact_digest(artifact: dict[str, Any]) -> str:
    """Bind title/content/location and source type; hash identifies bytes, NOT their truth."""
    data = {k: artifact[k] for k in ("title", "content", "source_location", "source_type")}
    return digest_text(json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")))


def elements(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [{**item, "element_type": field} for field in ELEMENT_FIELDS for item in state.get(field, [])]


def element_by_id(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {x["id"]: x for x in elements(state)}


def validate_state(state: dict[str, Any], require_approved: bool = True) -> dict[str, Any]:
    if not isinstance(state, dict):
        raise ValidationError("Decision state must be an object")
    required = ("episode_id", "decision_id", "decision", "repository", "accepted_at", "cutoff_at")
    for key in required:
        if not isinstance(state.get(key), str) or not state[key].strip():
            raise ValidationError(f"Missing/nonempty string required: state.{key}")
    if "::" in state["repository"]:
        raise ValidationError("Repository ID cannot contain reserved version-key separator '::'")
    if require_approved and state.get("human_approved") is not True:
        raise ValidationError("Authoritative S0 requires explicit human_approved=true")
    if parse_timestamp(state["accepted_at"]) >= parse_timestamp(state["cutoff_at"]):
        raise ValidationError("Decision accepted_at must be earlier than cutoff_at")
    result = deepcopy(state)
    result["accepted_at"], result["cutoff_at"] = iso(state["accepted_at"]), iso(state["cutoff_at"])
    ids: set[str] = set()
    for field in ELEMENT_FIELDS:
        collection = result.setdefault(field, [])
        if not isinstance(collection, list):
            raise ValidationError(f"state.{field} must be a list")
        for item in collection:
            if not isinstance(item, dict):
                raise ValidationError(f"state.{field}: each element must be an object")
            for key in ("id", "text", "source"):
                if not isinstance(item.get(key), str) or not item[key].strip():
                    raise ValidationError(f"state.{field} element missing {key}")
            if item["id"] in ids:
                raise ValidationError(f"Duplicate decision element ID: {item['id']}")
            ids.add(item["id"])
            if not isinstance(item.get("keywords", []), list):
                raise ValidationError("element.keywords must be a list")
    if not ids:
        raise ValidationError("S0 requires documented rationale elements")
    central = result.get("central_element_ids", [])
    if not isinstance(central, list) or not central or not all(isinstance(x, str) and x in ids for x in central):
        raise ValidationError("central_element_ids must be a nonempty list of existing element IDs")
    if len(set(central)) != len(central):
        raise ValidationError("central_element_ids contains duplicates")
    composite_groups = result.get("composite_groups", [])
    if not isinstance(composite_groups, list):
        raise ValidationError("composite_groups must be a list")
    for group in composite_groups:
        if not isinstance(group, dict) or not isinstance(group.get("original_id"), str):
            raise ValidationError("Invalid composite group")
        members = group.get("member_ids")
        if (not isinstance(members, list) or not members or
            not all(isinstance(m, str) and m in ids for m in members) or
            len(set(members)) != len(members)):
            raise ValidationError("Invalid composite member IDs")
        if group["original_id"] in ids:
            raise ValidationError("A decomposed composite cannot coexist with its atomic members")
    return result


def normalize_artifact(a: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(a, dict):
        raise ValidationError("Artifact must be a JSON object")
    b = deepcopy(a)
    for field in ("artifact_id", "repository", "source_type", "source_location", "title", "timestamp"):
        if not isinstance(b.get(field), str) or not b[field].strip():
            raise ValidationError(f"Artifact missing {field}")
    for field in ("artifact_id", "repository"):
        if "::" in b[field]:
            raise ValidationError(f"Reserved version-key separator '::' in artifact.{field}")
    if not isinstance(b.get("content"), str):
        raise ValidationError("Artifact.content must be a string")
    b["timestamp"] = iso(b["timestamp"])
    b["first_auditable_at"] = iso(b.get("first_auditable_at", b["timestamp"]))
    if parse_timestamp(b["first_auditable_at"]) < parse_timestamp(b["timestamp"]):
        raise ValidationError("Artifact cannot be auditable before its recorded event/version timestamp")
    computed_hash = artifact_digest(b)
    if b.get("content_sha256") and b["content_sha256"] != computed_hash:
        raise ValidationError(f"Artifact digest mismatch: {b['artifact_id']}")
    b["content_sha256"] = computed_hash
    b["version_id"] = str(b.get("version_id") or f"{b['first_auditable_at']}-{computed_hash[:16]}")
    if not b["version_id"].strip():
        raise ValidationError("Artifact.version_id cannot be empty")
    if "::" in b["version_id"]:
        raise ValidationError("Reserved version-key separator '::' in artifact.version_id")
    if not isinstance(b.get("tags", []), list):
        raise ValidationError("Artifact.tags must be a list")
    b.setdefault("tags", [])
    return b


def artifact_key(a: dict[str, Any]) -> str:
    return f"{a['repository']}::{a['artifact_id']}::{a['version_id']}"


def normalize_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(history, list):
        raise ValidationError("History must be a list")
    result: dict[str, dict[str, Any]] = {}
    for raw in history:
        item = normalize_artifact(raw)
        key = artifact_key(item)
        if key in result and item != result[key]:
            raise ValidationError(f"Conflicting entries for exact artifact version {key}")
        result[key] = item
    return sorted(result.values(), key=lambda x: (x["first_auditable_at"], artifact_key(x)))


def eligible(state: dict[str, Any], a: dict[str, Any]) -> bool:
    # This check is repeated after retrieval; search results are never authoritative.
    if a["repository"] != state["repository"]:
        return False
    accepted, cutoff, version_at = (parse_timestamp(state["accepted_at"]),
                                    parse_timestamp(state["cutoff_at"]),
                                    parse_timestamp(a["first_auditable_at"]))
    return accepted < version_at <= cutoff


def tokenize(text: str) -> set[str]:
    return {s for s in re.findall(r"[a-z0-9][a-z0-9_+-]+", str(text).lower()) if len(s) >= 3}


def quoted_from(a: dict[str, Any], quote: str) -> bool:
    return bool(isinstance(quote, str) and quote.strip() and
                quote in f"{a['title']}\n{a['content']}")
