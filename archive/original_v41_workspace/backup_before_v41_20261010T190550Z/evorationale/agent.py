"""Single bounded agent implementing the paper's retrieve-link-verify-memory-analyze-validate loop.

No automatic architectural decisions. Every run is reviewed by a human.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
import hashlib
import json
from datetime import datetime, timezone
import time
from typing import Any
from uuid import uuid4

from .analysis import ActionPlanner, composite_coverage
from .budget import Budget, BudgetExhausted
from .formal import NoAlloy
from .linking import ExplicitTextLinker
from .memory import DecisionMemory, MemoryInProcess
from .model import artifact_key, eligible, normalize_history, validate_state
from .planning import TemporalQueryPlanner
from .retrieval import LocalHybridRetriever
from .verification import EvidenceVerifier, ReportValidator


def _proposal_fingerprint(proposal: Any) -> str:
    """Exact, run-scoped verdict cache. A changed proposal requires new checking."""
    # Question ID and model confidence are not evidence; changed provenance,
    # relation, quote or target element still results in a cache miss.
    if isinstance(proposal, dict):
        proposal = {k: v for k, v in proposal.items()
                    if k not in {"question_id", "relation_confidence"}}
    packed = json.dumps(proposal, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(packed.encode("utf-8")).hexdigest()


@dataclass
class AgentRun:
    memory: DecisionMemory
    report: dict[str, Any]
    status: str

    @property
    def run_id(self) -> str:
        return self.memory.run_id

    @property
    def trace(self) -> list[dict[str, Any]]:
        return self.memory.trace


class EvoRationaleAgent:
    def __init__(self, *, retriever: Any = None, linker: Any = None,
                 evidence_verifier: Any = None, report_validator: Any = None,
                 planner: Any = None, action_planner: Any = None, store: Any = None,
                 formal_analyzer: Any = None, budget: Budget | None = None) -> None:
        self.retriever = retriever or LocalHybridRetriever()
        self.linker = linker or ExplicitTextLinker()
        self.evidence_verifier = evidence_verifier or EvidenceVerifier()
        self.report_validator = report_validator or ReportValidator()
        self.planner = planner or TemporalQueryPlanner()
        self.action_planner = action_planner or ActionPlanner()
        self.store = store or MemoryInProcess()
        self.formal_analyzer = formal_analyzer or NoAlloy()
        self.budget = budget or Budget()

    def run(self, initial_state: dict[str, Any], history: list[dict[str, Any]]) -> AgentRun:
        state = validate_state(initial_state)
        canonical_history = normalize_history(history)
        # Duplicate ids with distinct versions are legal, but only actual version keys may be cited.
        memory = DecisionMemory(run_id=str(uuid4()), initial_state=state,
                                needs=self.planner.initialize(state), status="RUNNING")
        self.store.save(memory)
        self.retriever.index(canonical_history)
        seen_new_artifact_streak = 0
        forced_stop = ""
        for index in range(self.budget.max_rounds):
            self.planner.update(memory)
            try:
                question = self.planner.select(state, memory)
            except BudgetExhausted as exc:
                forced_stop = str(exc)
                memory.verifier_feedback.append({"element_id": None, "reasons": [forced_stop]})
                self.store.save(memory)
                break
            if question is None:
                break
            memory.round_count += 1
            iteration_started = time.monotonic()
            prior_keys = set(memory.artifact_reads)
            try:
                self.budget.charge_query(memory)
                # Keep new-read capacity for later investigation rounds. Revisiting an
                # already fetched exact version is allowed only for a targeted need,
                # and capped, so it cannot crowd out unseen evidence indefinitely.
                # Retrieve more ranked *candidates* than the read cap: otherwise
                # later rounds can never discover lower-ranked unseen artifacts.
                retrieved = self.retriever.search(
                    state, question, limit=min(100, max(24, self.budget.max_artifact_reads * 3)),
                    sparse_candidates=self.budget.bm25_candidates,
                    dense_candidates=self.budget.dense_candidates, rrf_k=self.budget.rrf_k,
                )
                canonical = {artifact_key(a): a for a in canonical_history}
                allowed = []
                seen_hits = set()
                for candidate in retrieved:
                    key = artifact_key(candidate)
                    if key in seen_hits:
                        continue
                    seen_hits.add(key)
                    # Eligibility is verified against canonical history, not search metadata.
                    stored = canonical.get(key)
                    if (stored is None or candidate.get("content_sha256") != stored["content_sha256"]
                            or not eligible(state, stored)):
                        memory.verifier_feedback.append({"element_id": question["element_id"],
                            "artifact_key": key, "reasons": ["retriever_returned_noncanonical_artifact"]})
                        continue
                    allowed.append(stored)

                previously_read = set(memory.artifact_reads)
                remaining_rounds = self.budget.max_rounds - index
                remaining_reads = self.budget.max_artifact_reads - len(memory.artifact_reads)
                per_round_new_limit = ceil(remaining_reads / remaining_rounds)
                new_documents = [a for a in allowed if artifact_key(a) not in previously_read]
                new_documents = new_documents[:per_round_new_limit]
                replay_documents = []
                if question.get("element_id"):
                    target = question["element_id"]
                    already_supported = {x["artifact_key"] for x in memory.verified_links
                                         if x["decision_element_id"] == target}
                    # Two prior versions at most; an exact repeated proposal will
                    # be cached below instead of requiring another semantic judge.
                    replay_documents = [a for a in allowed
                        if artifact_key(a) in previously_read and artifact_key(a) not in already_supported][:2]

                candidate_documents = new_documents + replay_documents
                accepted_retrieval = []
                skipped_by_token_budget = []
                # Bound the payload BEFORE spending reads or calling external tools.
                for a in candidate_documents:
                    trial = {"state": state, "question": question,
                             "documents": accepted_retrieval + [a]}
                    if (memory.token_count + self.budget.estimate_tokens(trial)
                            <= self.budget.max_input_tokens):
                        accepted_retrieval.append(a)
                    else:
                        skipped_by_token_budget.append(artifact_key(a))
                if candidate_documents and not accepted_retrieval:
                    raise BudgetExhausted("cumulative_input_token_limit")
                self.budget.charge_tokens(memory, {"state": state, "question": question,
                                                   "documents": accepted_retrieval})
                fresh_keys = [artifact_key(a) for a in accepted_retrieval
                              if artifact_key(a) not in previously_read]
                self.budget.charge_reads(memory, fresh_keys)

                proposals = self.linker.propose(state, accepted_retrieval, question)
                self.budget.charge_tokens(memory, proposals)
                if not isinstance(proposals, list):
                    proposals = [proposals]
                newly_verified = 0
                newly_rejected = 0
                repeated_verdicts = 0
                for proposed_link in proposals:
                    fp = _proposal_fingerprint(proposed_link)
                    # Do not let a cached semantic judgment bypass numeric validation.
                    score = proposed_link.get("relation_confidence") if isinstance(proposed_link, dict) else None
                    valid_score = (isinstance(score, (int, float)) and not isinstance(score, bool)
                                   and 0 <= score <= 1)
                    if valid_score and fp in memory.reviewed_proposals:
                        repeated_verdicts += 1
                        continue
                    verified, feedback = self.evidence_verifier.verify(
                        state, canonical_history, [proposed_link])
                    # A transient judge failure is not a semantic rejection. It
                    # may be retried later; only genuine verdicts are cached.
                    technical = [f for f in feedback if any(
                        str(reason).startswith("semantic_judge_error:")
                        for reason in f.get("reasons", []))]
                    if valid_score and not technical:
                        memory.reviewed_proposals[fp] = {
                            "accepted": bool(verified), "feedback": feedback,
                        }
                    before = len(memory.verified_links)
                    for link in verified:
                        memory.record_link(link)
                    newly_verified += len(memory.verified_links) - before
                    newly_rejected += len(feedback)
                    memory.verifier_feedback.extend(feedback)
                    memory.technical_verification_failures.extend(technical)
                    memory.rejected_interpretations.extend(
                        f for f in feedback if f not in technical)
                self.planner.update(memory)
                outstanding = self.planner.required_open(memory)
                report = self.action_planner.compose(state, memory.verified_links, outstanding, memory=memory)
                result = self.report_validator.validate(state, memory.verified_links, report)
                report["verification"] = result
                report["unsupported_claim_rate"] = result["unsupported_claim_rate"]
                report["zero_claim_report"] = not bool(memory.verified_links)
                if result["status"] != "PASS":
                    memory.verifier_feedback.append({"element_id": question["element_id"],
                                                     "reasons": result["failures"]})
                delta = len(set(memory.artifact_reads) - prior_keys)
                if delta == 0:
                    seen_new_artifact_streak += 1
                else:
                    seen_new_artifact_streak = 0
                memory.trace.append({"at": datetime.now(timezone.utc).isoformat(),
                    "round": index + 1, "question": question,
                    "retrieved_artifact_keys": [artifact_key(a) for a in accepted_retrieval],
                    "new_artifact_keys": fresh_keys,
                    "reused_artifact_keys": [artifact_key(a) for a in accepted_retrieval
                                             if artifact_key(a) in previously_read],
                    "skipped_due_to_token_budget": skipped_by_token_budget,
                    "verified_links_added": newly_verified,
                    "verifier_rejections": newly_rejected,
                    "cached_verifier_decisions": repeated_verdicts,
                    "unresolved_required": [x["id"] for x in outstanding],
                    "verification": result["status"],
                    "elapsed_ms": round((time.monotonic()-iteration_started)*1000, 2)})
                memory.report = report
                self.store.save(memory)
                if not outstanding and result["status"] == "PASS":
                    break
                if seen_new_artifact_streak >= 2:
                    forced_stop = "two_searches_with_no_new_artifact"
                    break
            except BudgetExhausted as exc:
                forced_stop = str(exc)
                memory.verifier_feedback.append({"element_id": question["element_id"],
                                                 "reasons": [forced_stop]})
                memory.trace.append({"round": index+1, "question": question,
                                     "verification": "BUDGET_EXHAUSTED", "reason": forced_stop})
                self.store.save(memory)
                break
        self.planner.update(memory)
        unresolved = self.planner.required_open(memory)
        report = self.action_planner.compose(state, memory.verified_links, unresolved, bool(forced_stop), memory=memory)
        validation = self.report_validator.validate(state, memory.verified_links, report)
        if validation["status"] != "PASS":
            # Reject the entire proposed report; never present an unsupported recommendation.
            original_failures = list(validation["failures"])
            report = ActionPlanner().compose(state, memory.verified_links,
                       unresolved or [{"question": "The proposed report failed independent validation."}], True)
            report["model_proposal_rejected"] = original_failures
            validation = self.report_validator.validate(state, memory.verified_links, report)
            forced_stop = forced_stop or "independent_report_validation_failed"
        report["zero_claim_report"] = not bool(memory.verified_links)
        if not memory.verified_links or unresolved:
            # Do not conflate incomplete investigation with unsupported *claims*.
            # A zero-claim or otherwise invalid report retains the original UCR=1 rule.
            incomplete_ucr = validation["unsupported_claim_rate"]
            report["verification"] = {**validation, "status": "UNRESOLVED",
                                     "unsupported_claim_rate": incomplete_ucr,
                                     "investigation_complete": False,
                                     "failures": validation["failures"] + ([forced_stop] if forced_stop else [])}
            report["unsupported_claim_rate"] = incomplete_ucr
            report["recommended_outcome"] = "REVALIDATE"
            report["next_action"] = "Collect additional verified evidence; the agent did not establish complete revalidation."
        else:
            report["verification"] = {**validation, "investigation_complete": True}
            report["unsupported_claim_rate"] = validation["unsupported_claim_rate"]
        report["composite_coverage"] = composite_coverage(state, memory.verified_links)
        report["formal_evidence"] = self.formal_analyzer.analyze(state)
        report["human_review_required"] = True
        report["human_review_status"] = "PENDING"
        report["budget_usage"] = {"rounds": memory.round_count, "queries": memory.query_count,
                                  "unique_artifact_reads": len(memory.artifact_reads),
                                  "estimated_input_tokens": memory.token_count}
        report["stopping_reason"] = forced_stop or ("verified_evidence_sufficient" if not unresolved else "round_limit_or_unresolved")
        memory.report = report
        memory.status = "AWAITING_HUMAN_REVIEW"
        self.store.save(memory)
        return AgentRun(memory=memory, report=report, status=memory.status)
