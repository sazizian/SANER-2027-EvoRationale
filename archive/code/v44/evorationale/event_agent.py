"""Opt-in event review that separates source reads from semantic coverage."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .agent import AgentRun
from .analysis import ActionPlanner
from .budget import Budget, BudgetExhausted
from .event_context import select_event_batches
from .formal import NoAlloy
from .memory import DecisionMemory, MemoryInProcess
from .model import artifact_key, eligible, normalize_history, validate_state
from .planning import TemporalQueryPlanner
from .verification import ReportValidator


class RequestBudgetTracker:
    """Reserves complete request-envelope estimates before every provider call.

    This is a conservative UTF-8 estimator, not the provider's tokenizer or
    a guarantee about billing. Reported provider usage is recorded separately.
    """
    def __init__(self, budget: Budget, memory: DecisionMemory) -> None:
        self.budget, self.memory = budget, memory
        self.requests: list[dict[str, Any]] = []

    def __call__(self, request: dict[str, Any]) -> None:
        output_tokens = request.get("max_output_tokens")
        if (type(output_tokens) is not int or not 0 < output_tokens <= self.budget.max_output_tokens):
            raise BudgetExhausted("per_request_output_token_limit")
        estimate = self.budget.estimate_tokens(request)
        self.budget.charge_tokens(self.memory, request)
        self.requests.append({"estimated_input_tokens": estimate,
                              "max_output_tokens": request.get("max_output_tokens"),
                              "model": request.get("model"), "response_received": False})

    def record_response(self, response: Any) -> None:
        record = self.requests[-1]
        record["response_received"] = True
        usage = getattr(response, "usage", None)
        for name in ("input_tokens", "output_tokens", "total_tokens"):
            value = usage.get(name) if isinstance(usage, dict) else getattr(usage, name, None)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                record["provider_" + name] = value

    def summary(self) -> dict[str, Any]:
        return {"accounting": "REQUEST_ENVELOPE_ESTIMATE_INCLUDING_RETRIES_NOT_BILLING",
                "max_output_tokens_per_request": self.budget.max_output_tokens,
                "provider_requests_reserved": len(self.requests),
                "provider_responses_received": sum(r["response_received"] for r in self.requests),
                "responses_with_reported_usage": sum("provider_input_tokens" in r for r in self.requests),
                "provider_reported_input_tokens": sum(r.get("provider_input_tokens", 0) for r in self.requests),
                "provider_reported_output_tokens": sum(r.get("provider_output_tokens", 0) for r in self.requests),
                "requests": self.requests}


class EventReviewAgent:
    def __init__(self, *, linker: Any, judge: Any, store: Any = None,
                 budget: Budget | None = None, formal_analyzer: Any = None) -> None:
        self.linker, self.judge = linker, judge
        self.store = store or MemoryInProcess()
        self.budget = budget or Budget(max_output_tokens=16384)
        self.formal_analyzer = formal_analyzer or NoAlloy()

    def run(self, initial_state: dict[str, Any], history: list[dict[str, Any]]) -> AgentRun:
        state = validate_state(initial_state)
        canonical = normalize_history(history)
        allowed = [a for a in canonical if eligible(state, a)]
        memory = DecisionMemory(run_id=str(uuid4()), initial_state=state,
                                needs=TemporalQueryPlanner().initialize(state), status="RUNNING")
        tracker = RequestBudgetTracker(self.budget, memory)
        batches = select_event_batches(state, canonical, self.budget.max_artifact_reads)
        review_records: list[dict[str, Any]] = []
        forced_stop = ""
        self.store.save(memory)
        for batch in batches:
            if memory.round_count >= self.budget.max_rounds:
                forced_stop = "event_round_limit"
                break
            memory.round_count += 1
            keys = [artifact_key(a) for a in batch]
            trace: dict[str, Any] = {
                "at": datetime.now(timezone.utc).isoformat(), "round": memory.round_count,
                "profile": "event-complete", "retrieved_artifact_keys": keys,
                "reviewed_artifact_ids": [], "proposal_count": 0,
                "verified_links_added": 0, "verifier_rejections": 0,
            }
            try:
                self.budget.charge_query(memory)
                self.budget.charge_reads(memory, keys)
                # Every selected source is reviewed against all S0 elements.
                # Central-need resolution does not suppress remaining hunks.
                proposals = self.linker.propose_event(state, batch, charge=tracker)
                records = list(self.linker.last_reviews)
                review_records.extend(records)
                trace["reviewed_artifact_ids"] = [r["artifact_id"] for r in records]
                trace["artifact_reviews"] = records
                trace["proposal_count"] = len(proposals)
                trace["proposed_links"] = proposals
                accepted, feedback = self.judge.review_event(state, batch, proposals, charge=tracker)
                before = len(memory.verified_links)
                for link in accepted:
                    memory.record_link(link)
                memory.verifier_feedback.extend(feedback)
                technical = [f for f in feedback if any(str(reason).startswith("semantic_judge_error:")
                                                       for reason in f.get("reasons", []))]
                memory.technical_verification_failures.extend(technical)
                memory.rejected_interpretations.extend(f for f in feedback if f not in technical)
                trace["verified_links_added"] = len(memory.verified_links) - before
                trace["verifier_rejections"] = len(feedback) - len(technical)
                trace["technical_verification_failures"] = len(technical)
                trace["verification"] = "UNRESOLVED" if technical else "EVENT_REVIEW_COMPLETED"
            except BudgetExhausted as exc:
                forced_stop = str(exc)
                trace["verification"] = "BUDGET_EXHAUSTED"
                trace["reason"] = forced_stop
                memory.verifier_feedback.append({"element_id": None, "reasons": [forced_stop]})
            except Exception as exc:
                # An incomplete model batch is a technical coverage failure,
                # never a semantic no-effect verdict for unseen source rows.
                reason = "semantic_judge_error:event_review:" + getattr(exc, "code", type(exc).__name__)
                failure = {"element_id": None, "artifact_keys": keys, "reasons": [reason]}
                memory.verifier_feedback.append(failure)
                memory.technical_verification_failures.append(failure)
                contract_failures = list(getattr(self.linker, "last_proposal_rejections", []))
                if contract_failures:
                    memory.verifier_feedback.extend(contract_failures)
                    memory.technical_verification_failures.extend(contract_failures)
                    trace["linker_contract_failures"] = contract_failures
                trace["verification"] = "TECHNICAL_REVIEW_FAILURE"
                trace["reason"] = reason
            memory.trace.append(trace)
            self.store.save(memory)
            if forced_stop:
                break

        for need in memory.needs:
            if need["element_id"] is None:
                need["status"] = "REVIEWED" if review_records else "OPEN"
                continue
            links = [l for l in memory.verified_links if l["decision_element_id"] == need["element_id"]]
            whole = [l for l in links if l["relation"] == "supports"
                     and l.get("semantic_assessment", {}).get("whole_element_supported") is True
                     and l.get("semantic_assessment", {}).get("claim_scope") == "whole_element"]
            adverse = any(l["relation"] != "supports" for l in links)
            conflicting = adverse and len({l["relation"] for l in links}) > 1
            need["status"] = ("CONFLICTING_EVIDENCE" if conflicting else "ADVERSE_EVIDENCE" if adverse
                              else "RESOLVED" if whole
                              else "PARTIAL_EVIDENCE" if links else "OPEN")
            need["attempts"] = sum(need["element_id"] in r.get("considered_element_ids", [])
                                   for r in review_records)
        # An accepted adverse link answers a need with evidence of change; it
        # does not claim whole-element support. Only unknown, partial-positive,
        # or conflicting needs are gaps requiring revalidation. Otherwise every
        # verified adverse event would be forced to REVALIDATE forever.
        answered = {"RESOLVED", "ADVERSE_EVIDENCE"}
        unresolved = [n for n in memory.needs if n["required"] and n["status"] not in answered]
        reviewed_keys = {r["artifact_key"] for r in review_records}
        unreviewed = [a["artifact_id"] for a in allowed if artifact_key(a) not in reviewed_keys]
        uncertain_reviews = [r["artifact_id"] for r in review_records
                             if r.get("status") == "insufficient_evidence"
                             or r.get("context_complete") is False
                             or r.get("citation_coverage_complete") is False]
        report_gaps = list(unresolved)
        if unreviewed or uncertain_reviews or memory.technical_verification_failures or forced_stop:
            report_gaps.append({"id": "source-review-coverage", "required": True,
                                "element_id": None, "question": "Resolve incomplete or uncertain source reviews."})
        if not state.get("original_evidence"):
            report_gaps.append({"id": "initial-rationale-coverage", "required": True,
                                "element_id": None, "question": "Document the accepted decision's original rationale evidence."})
        incomplete = bool(report_gaps or unreviewed or uncertain_reviews or memory.technical_verification_failures
                          or forced_stop or not state.get("original_evidence"))
        # Compose from the complete uncertainty set BEFORE validation; changing
        # an outcome afterwards would leave its probability vector inconsistent.
        report = ActionPlanner().compose(state, memory.verified_links, report_gaps, bool(forced_stop))
        validation = ReportValidator().validate(state, memory.verified_links, report)
        failures = list(validation["failures"])
        if forced_stop:
            failures.append(forced_stop)
        report["verification"] = {**validation,
                                  "status": "UNRESOLVED" if incomplete else validation["status"],
                                  "investigation_complete": not incomplete, "failures": failures}
        if incomplete:
            report["recommended_outcome"] = "REVALIDATE"
            report["next_action"] = "Review remaining rationale coverage and source-qualified evidence with a human."
        report["unsupported_claim_rate"] = validation["unsupported_claim_rate"]
        report["investigation_profile"] = "event-complete"
        report["stopping_reason"] = forced_stop or ("selected_artifacts_reviewed" if not unreviewed
                                                     else "bounded_artifact_selection_completed")
        report["budget_usage"] = {"rounds": memory.round_count, "queries": memory.query_count,
                                  "unique_artifact_reads": len(memory.artifact_reads),
                                  "estimated_input_tokens": memory.token_count,
                                  **tracker.summary()}
        report["investigation_coverage"] = {
            "eligible_artifact_versions": len(allowed),
            "selected_artifact_versions": sum(len(b) for b in batches),
            "source_versions_read": len(memory.artifact_reads),
            "model_reported_reviewed_artifact_versions": len(reviewed_keys),
            "not_semantically_reviewed_artifact_ids": unreviewed,
            "unresolved_artifact_review_ids": uncertain_reviews,
            "artifact_review_records": review_records,
            "all_need_statuses": memory.needs,
            "required_unresolved_element_ids": [n["element_id"] for n in unresolved],
            "note": "Source reads and model-reported review coverage are not semantic correctness or whole-element support.",
        }
        report["formal_evidence"] = self.formal_analyzer.analyze(state)
        report["human_review_required"] = True
        report["human_review_status"] = "PENDING"
        report["zero_claim_report"] = not bool(memory.verified_links)
        memory.report, memory.status = report, "AWAITING_HUMAN_REVIEW"
        self.store.save(memory)
        return AgentRun(memory=memory, report=report, status=memory.status)
