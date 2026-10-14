"""Propose an S0 draft from sourced architecture decision records; human approval is mandatory.

This builder does not invent undocumented rationale. Automatic initial-state quality was
NOT evaluated in the paper and is NOT represented as experimentally validated here.
"""
from __future__ import annotations

from copy import deepcopy
import re
from typing import Any
from .model import artifact_key, normalize_artifact, validate_state

SECTION_MAP = {
    "context": "assumptions", "assumption": "assumptions", "assumptions": "assumptions",
    "goal": "goals", "goals": "goals", "requirement": "requirements", "requirements": "requirements",
    "evidence": "original_evidence", "benchmark": "original_evidence",
    "quality": "quality_attributes", "constraints": "constraints_dependencies",
    "constraint": "constraints_dependencies", "dependencies": "constraints_dependencies",
    "implementation": "implementation_scope", "scope": "implementation_scope",
}


def draft_from_anchor(anchor: dict[str, Any], cutoff_at: str, episode_id: str) -> dict[str, Any]:
    a = normalize_artifact(anchor)
    accepted = a["first_auditable_at"]
    result: dict[str, Any] = {
        "episode_id": episode_id, "decision_id": a["artifact_id"],
        "decision": a["title"], "repository": a["repository"],
        "accepted_at": accepted, "cutoff_at": cutoff_at,
        "human_approved": False, "central_element_ids": [], "builder_status": "DRAFT_REQUIRES_HUMAN_REVIEW",
        "anchor_key": artifact_key(a), "unresolved_rationale_questions": [],
    }
    for value in SECTION_MAP.values():
        result[value] = []
    current: str | None = None
    for line in a["content"].splitlines():
        # Only explicit section-labelled lines are candidates. Missing sections are unknown.
        match = re.match(r"^\s{0,3}(?:#{1,4}\s*)?([\w -]+)\s*:\s*(.*)$", line)
        if match:
            field = SECTION_MAP.get(match.group(1).lower().strip())
            if field:
                current = field
                if match.group(2).strip():
                    result[field].append(_element(a, field, match.group(2).strip(), len(result[field]) + 1))
                continue
        if current and line.strip().startswith(("- ", "* ")):
            result[current].append(_element(a, current, line.strip()[2:], len(result[current]) + 1))
    for field in set(SECTION_MAP.values()):
        if not result[field]:
            result["unresolved_rationale_questions"].append(f"Find documented {field} for {a['artifact_id']}")
    return result


def _element(a: dict[str, Any], field: str, text: str, index: int) -> dict[str, Any]:
    return {"id": field.upper()[:3] + str(index), "text": text, "source": a["source_location"],
            "source_artifact_key": artifact_key(a), "source_version_sha256": a["content_sha256"],
            "extraction_kind": "EXPLICIT_SECTION", "keywords": []}


def approve_draft(draft: dict[str, Any], central_element_ids: list[str]) -> dict[str, Any]:
    # Only invoke after a real authorized human has checked sources. Not an automated action.
    updated = deepcopy(draft)
    updated["central_element_ids"] = central_element_ids
    updated["human_approved"] = True
    updated["human_review_required"] = True
    return validate_state(updated)
