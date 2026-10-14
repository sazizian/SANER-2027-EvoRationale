"""Human-only actions and an immutable review log; AI cannot authorize changes to S0."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from typing import Any
from .memory import MemoryStore
from .model import validate_state

ACTIONS={"ACCEPT", "REVISE", "REJECT", "REQUEST_EVIDENCE"}


def record_human_review(store: MemoryStore, run_id: str, *, reviewer_id: str,
                        action: str, note: str, approved_new_state: dict[str, Any] | None = None) -> dict[str, Any]:
    if action not in ACTIONS:
        raise ValueError("Invalid human action")
    if not reviewer_id.strip() or not note.strip():
        raise ValueError("Review must identify a human and include a reason")
    run=store.get(run_id)
    if run is None or run.report is None or run.status!='AWAITING_HUMAN_REVIEW':
        raise ValueError("No pending report exists for human review")
    if approved_new_state is not None and action not in {"ACCEPT","REVISE"}:
        raise ValueError("Cannot attach a new state for a rejected or evidence-requested report")
    if approved_new_state is not None:
        state=validate_state(approved_new_state)
        if state['decision_id']!=run.initial_state['decision_id']:
            raise ValueError("Approved state must apply to the same decision")
        fingerprint=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
    else:
        fingerprint=None
    review={"reviewer_id":reviewer_id,"action":action,"note":note,
            "at":datetime.now(timezone.utc).isoformat(),
            "original_run_id":run_id, "approved_new_state_sha256":fingerprint}
    run.human_reviews.append(review)
    run.status='HUMAN_REVIEWED'
    run.report['human_review_status']=action
    # The caller, NOT this agent, is responsible for committing the new S0
    # through an authorized repository workflow after explicit human approval.
    store.save(run)
    return review
