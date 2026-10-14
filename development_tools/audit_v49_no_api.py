#!/usr/bin/env python3
"""Exercise complete pair-review request envelopes using local transport only.

Only approved fixed S0, unlabeled history and optional preparation identity are
read. Complete negative fixture rows measure request structure, never semantic
accuracy. A separately labelled positive-candidate/checker fixture forecasts
the conditional second phase without promoting any fixture into evidence.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_v48_no_api import DECISION_NAME, HISTORY_NAME, _sha, validate_catalog
from evorationale.budget import Budget
from evorationale.delta_context import build_delta_catalog
from evorationale.diff_context import DIFF_SOURCE_TYPES
from evorationale.event_context import select_event_batches
from evorationale.event_verification import _outbound
from evorationale.model import artifact_key, eligible, elements, normalize_history, validate_state
from evorationale.pair_review_verification import FINAL_RELATIONS, MAX_CANDIDATES, PairReviewSemanticJudge
from evorationale.structured_json import request_json_object

PROFILE = "event-pair-reviewed"
KIND = "DEVELOPMENT_ONLY_V49_EVENT_PAIR_REVIEWED_COMPARISON"
PRIMARY_NAME = "independent_fixed_s0_pair_review"
CHECKER_NAME = "independent_fixed_s0_pair_candidate_check"
REASON = "LOCAL TRANSPORT FIXTURE ONLY: no architectural relation has been assessed."


class _FakeResponses:
    """No SDK, credentials or network; complete explicit negative pair rows."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

    def create(self, **request: Any) -> SimpleNamespace:
        self.requests.append(deepcopy(request))
        payload = json.loads(request["input"])
        name = request["text"]["format"]["name"]
        if name != PRIMARY_NAME:
            raise AssertionError("Negative fixture unexpectedly invoked candidate checker")
        ids = [element["id"] for element in payload["fixed_s0"]["elements"]]
        result = {"considered_element_ids": ids,
                  "reviews": [{"artifact_handle": handle,
                               "status": "no_material_relation", "reason": REASON,
                               "support_reason": REASON, "change_reason": REASON,
                               "links": [],
                               "pair_outcomes": [{"element_id": target, "outcome": "no_relation",
                                                  "reason": REASON, "relations": []}
                                                 for target in ids]}
                              for handle in payload["review_artifact_handles"]]}
        return SimpleNamespace(status="completed", output_text=json.dumps(result))


class _RejectCheckerResponses:
    """Capacity fixture only: every hypothetical candidate is rejected."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

    def create(self, **request: Any) -> SimpleNamespace:
        self.requests.append(deepcopy(request))
        if request["text"]["format"]["name"] != CHECKER_NAME:
            raise AssertionError("Checker capacity fixture invoked unexpected phase")
        payload = json.loads(request["input"])
        result = {"decisions": [{"candidate_id": candidate["candidate_id"], "verdict": "reject",
                                  "reason": REASON, "predicate_reason": REASON,
                                  "contribution_reason": REASON, "authority_reason": REASON}
                                 for candidate in payload["candidate_hypotheses"]]}
        return SimpleNamespace(status="completed", output_text=json.dumps(result))


def _checker_capacity_fixture(catalog: dict[str, Any], state: dict[str, Any],
                              model: str, output_limit: int) -> tuple[dict[str, Any] | None, int]:
    """Forecast the checker using source-owned maximum proof-list hypotheses.

    These are not primary predictions or meaningful relation assessments. For
    each structurally available artifact/target/relation combination use its
    complete target text, every mechanically allowed local side handle and all
    same-event context handles. The largest 64 serialized combinations form a
    conservative input-envelope capacity scenario; primary output ceilings may
    make this entire scenario impossible to emit. No expected label is read.
    """
    combinations = []
    context_handles = list(catalog["lines"])
    for artifact_handle, artifact in catalog["artifacts"].items():
        passages = [h for h, p in catalog["passages"].items() if p["artifact_handle"] == artifact_handle]
        if not passages:
            continue
        own = [(h, line) for h, line in catalog["lines"].items()
               if line["artifact_handle"] == artifact_handle]
        diff = artifact["source_type"] in DIFF_SOURCE_TYPES
        before = [h for h, line in own if diff and line["role"] in {"removed", "unchanged"}]
        after = [h for h, line in own
                 if line["role"] in ({"added", "unchanged"} if diff else {"statement"})]
        for target in elements(state):
            for relation in sorted(FINAL_RELATIONS):
                hypothesis = {"candidate_id": "C0001", "artifact_handle": artifact_handle,
                              "element_id": target["id"], "relation": relation,
                              "s0_claim_quote": _outbound(target["text"]),
                              "passage_handle": max(passages, key=len),
                              "before_line_handles": before, "after_line_handles": after,
                              "context_line_handles": context_handles, "claim_scope": "material_subclaim"}
                size = len(json.dumps(hypothesis, ensure_ascii=False).encode("utf-8"))
                combinations.append((size, hypothesis))
    combinations.sort(key=lambda item: item[0], reverse=True)
    candidates = [deepcopy(hypothesis) for _, hypothesis in combinations[:MAX_CANDIDATES]]
    for number, candidate in enumerate(candidates, 1):
        candidate["candidate_id"] = f"C{number:04d}"
    if not candidates:
        return None, 0
    fake = _RejectCheckerResponses()
    judge = PairReviewSemanticJudge(model, client=SimpleNamespace(responses=fake))
    result = request_json_object(client=judge.client, model=model, effort=judge.effort,
        **judge.candidate_request_spec(catalog, candidates), output_token_ceiling=min(16384, output_limit),
        attempts=2)
    decisions = judge._validate_candidate_response(result, candidates)
    if len(fake.requests) != 1 or any(d["verdict"] != "reject" for d in decisions.values()):
        raise AssertionError("Checker capacity fixture unexpectedly retried or confirmed evidence")
    request = fake.requests[0]
    payload = json.loads(request["input"])
    if payload["original_catalog"] != catalog["payload"]:
        raise ValueError("Checker request omits or alters original full same-event context")
    return request, len(candidates)


def _validate_parameters(models: Any, budgets: Any, nomination_mode: str) -> int:
    if (not isinstance(models, dict) or set(models) != {"linker", "judge"}
            or any(not isinstance(v, str) or not v.strip() for v in models.values())):
        raise ValueError("Expected explicit opaque linker and judge model IDs")
    names = ("max_rounds", "max_queries", "max_reads", "max_input_tokens", "max_provider_requests")
    if (not isinstance(budgets, dict)
            or any(type(budgets.get(n)) is not int or budgets[n] < 1 for n in names)):
        raise ValueError("Expected positive integer evaluation and provider-request budgets")
    output_limit = budgets.get("max_output_tokens", 16384)
    if type(output_limit) is not int or output_limit < 1:
        raise ValueError("Expected positive integer output-token budget")
    if nomination_mode != "none":
        raise ValueError("The event-pair-reviewed profile requires nomination mode none")
    return output_limit


def audit_sources(state_input: dict[str, Any], history_input: list[dict[str, Any]],
                  models: dict[str, str], budgets: dict[str, int], *,
                  nomination_mode: str = "none") -> dict[str, Any]:
    """Forecast full negative pair-review envelopes without a provider call."""
    output_limit = _validate_parameters(models, budgets, nomination_mode)
    original_inputs = deepcopy((state_input, history_input))
    state = validate_state(state_input)
    history = normalize_history(history_input)
    allowed = [artifact for artifact in history if eligible(state, artifact)]
    selected = select_event_batches(state, history, budgets["max_reads"])
    active = selected[:min(budgets["max_rounds"], budgets["max_queries"])]
    fake = _FakeResponses()
    judge = PairReviewSemanticJudge(models["judge"], client=SimpleNamespace(responses=fake))

    # Forecast every selected envelope even if a configured cumulative budget
    # would stop a hosted run. Both exhaustion points are explicitly reported.
    def forecast_only(_request: Any) -> None:
        pass
    forecast_only.budget = SimpleNamespace(max_output_tokens=output_limit)

    envelopes: list[dict[str, Any]] = []
    checker_envelopes: list[dict[str, Any]] = []
    checker_requests: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    cumulative = 0
    first_unaffordable = None
    first_over_provider_limit = None
    reviewed_keys: set[str] = set()
    element_ids = {element["id"] for element in elements(state)}
    for number, batch in enumerate(active, 1):
        catalog = build_delta_catalog(state, batch)
        checks = validate_catalog(catalog, batch)
        before = len(fake.requests)
        accepted, rejected = judge.review_event(state, batch, [], charge=forecast_only)
        if accepted or rejected:
            raise AssertionError("Negative transport fixture produced evidence or rejection")
        requests = fake.requests[before:]
        focus_seen: list[str] = []
        for request in requests:
            if request["text"]["format"]["name"] != PRIMARY_NAME:
                raise AssertionError("Unexpected provider phase in negative pair scenario")
            payload = json.loads(request["input"])
            focuses = payload.get("review_artifact_handles")
            if (not isinstance(focuses, list) or not 1 <= len(focuses) <= 3
                    or len(set(focuses)) != len(focuses)):
                raise ValueError("Primary review focus is not a bounded unique artifact chunk")
            expected_payload = {**catalog["payload"], "review_artifact_handles": focuses,
                                "expected_artifact_target_pairs": len(focuses) * len(element_ids)}
            if payload != expected_payload:
                raise ValueError("Primary request omits or alters full validated same-event context")
            focus_seen.extend(focuses)
            estimate = Budget.estimate_tokens(request)
            cumulative += estimate
            if first_unaffordable is None and cumulative > budgets["max_input_tokens"]:
                first_unaffordable = {"batch": number, "stage": "primary",
                                      "cumulative_estimated_input_tokens": cumulative}
            if first_over_provider_limit is None and len(envelopes) + 1 > budgets["max_provider_requests"]:
                first_over_provider_limit = {"batch": number, "stage": "primary",
                                             "provider_request_number": len(envelopes) + 1}
            envelopes.append({"batch": number, "stage": "primary", "focused_artifacts": focuses,
                              "expected_pair_rows": len(focuses) * len(element_ids),
                              "estimated_input_tokens": estimate,
                              "cumulative_estimated_input_tokens": cumulative,
                              "max_output_tokens": request["max_output_tokens"], "model": request["model"],
                              "request_sha256": _sha(json.dumps(request, sort_keys=True,
                                                                ensure_ascii=False).encode("utf-8")),
                              "includes_full_schema_and_instructions": True,
                              "all_same_event_source_artifacts_visible": True,
                              "mock_response_received": True})
        if focus_seen != list(catalog["artifacts"]):
            raise ValueError("Primary chunks do not review every exact source artifact once")
        reviews = judge.last_reviews
        if len(reviews) != len(batch) or not all(
                set(review["considered_element_ids"]) == element_ids for review in reviews):
            raise ValueError("Incomplete mocked fixed-S0 artifact reviews")
        checker_request, candidate_count = _checker_capacity_fixture(catalog, state, models["judge"], output_limit)
        checker_estimate = 0
        if checker_request is not None:
            checker_requests.append(checker_request)
            checker_estimate = Budget.estimate_tokens(checker_request)
            checker_envelopes.append({"batch": number, "stage": "checker_capacity_forecast",
                "hypothetical_candidates": candidate_count, "estimated_input_tokens": checker_estimate,
                "max_output_tokens": checker_request["max_output_tokens"], "model": checker_request["model"],
                "request_sha256": _sha(json.dumps(checker_request, sort_keys=True, ensure_ascii=False).encode("utf-8")),
                "includes_full_schema_and_instructions": True,
                "all_same_event_source_artifacts_visible": True, "mock_response_received": True,
                "fixture_verdicts": "ALL_REJECT", "semantic_claim_available": False,
                "maximum_local_side_handles_and_full_context_handles_used": True})
        reviewed_keys.update(artifact_key(artifact) for artifact in batch)
        rows.append({"batch": number, "artifact_ids": [a["artifact_id"] for a in batch],
                     "artifact_versions": len(batch), "source_bytes": catalog["context"]["source_bytes"],
                     "event_context_complete": catalog["context"]["complete"],
                     "primary_chunks": len(requests), "checker_chunks": 0,
                     "checker_capacity_forecast_calls": int(checker_request is not None),
                     "checker_capacity_forecast_candidates": candidate_count,
                     "checker_capacity_forecast_estimated_input_tokens": checker_estimate,
                     "explicit_pair_rows": len(batch) * len(element_ids),
                     "all_fixed_targets_explicitly_reviewed_by_mock": True,
                     "full_same_event_context_preserved_per_chunk": True,
                     "all_outbound_citation_coverage_complete": all(catalog["citation_coverage"].values()),
                     "incomplete_outbound_citation_artifact_ids": [catalog["artifacts"][h]["artifact_id"]
                         for h, complete in catalog["citation_coverage"].items() if not complete], **checks})
    if (state_input, history_input) != original_inputs:
        raise AssertionError("Source-only audit mutated supplied inputs")
    checker_total = sum(r["estimated_input_tokens"] for r in checker_envelopes)
    combined_total = cumulative + checker_total
    projected_calls = len(envelopes) + len(checker_envelopes)
    # Estimate the larger bounded retry by replacing only its actual output
    # allowance in each complete request envelope. This is a capacity forecast;
    # no fixture retry or real request is issued.
    retry_estimate = 0
    for request in fake.requests + checker_requests:
        retry = {**request, "max_output_tokens": min(16384, output_limit)}
        retry_estimate += Budget.estimate_tokens(retry)
    return {"status": "V49_SOURCE_ONLY_SYNTHETIC_PREFLIGHT_COMPLETED_NO_API_CALLED",
            "investigation_profile": PROFILE, "nomination_mode": nomination_mode,
            "semantic_result_available": False, "f1_available": False,
            "gold_labels_read": False, "provider_calls": 0,
            "mock_transport_calls": len(fake.requests) + len(checker_requests),
            "negative_scenario_mock_transport_calls": len(fake.requests),
            "mock_checker_capacity_forecast_requests": len(checker_requests), "mock_nomination_requests": 0,
            "mock_primary_requests": len(fake.requests), "mock_checker_requests": 0, "mock_retries": 0,
            "phase_estimated_input_tokens": {"primary": cumulative, "checker": 0},
            "conditional_phase_estimated_input_tokens": {"primary": cumulative, "checker": checker_total},
            "approval_mode": "APPROVED_RUNTIME_INPUT_REQUIRED",
            "input_human_approved": state_input.get("human_approved"), "state_approval_changed": False,
            "scenario": "COMPLETE_EXPLICIT_NEGATIVE_PAIR_ROWS_NO_CANDIDATES_NO_CHECKER_NO_RETRIES",
            "budget_estimator": "FULL_REQUEST_ENVELOPE_UTF8_ESTIMATE_NOT_PROVIDER_TOKENIZER_OR_PRICE",
            "models": models, "nominal_budgets": budgets,
            "historical_input_budget": 100000, "input_budget_change": budgets["max_input_tokens"] - 100000,
            "input_budget_increased_from_v48": budgets["max_input_tokens"] > 100000,
            "max_output_tokens_per_request": output_limit,
            "eligible_artifact_versions": len(allowed), "selected_batches": len(selected),
            "round_and_query_bounded_batches": len(active),
            "structurally_reviewable_artifact_versions": len(reviewed_keys),
            "structurally_reviewable_diff_versions": sum(a["source_type"] in DIFF_SOURCE_TYPES
                and artifact_key(a) in reviewed_keys for a in allowed),
            "outside_round_query_read_selection_ids": [a["artifact_id"] for a in allowed
                                                       if artifact_key(a) not in reviewed_keys],
            "scenario_estimated_input_tokens": cumulative,
            "scenario_within_nominal_estimate_budget": cumulative <= budgets["max_input_tokens"],
            "scenario_within_provider_request_budget": len(fake.requests) <= budgets["max_provider_requests"],
            "first_unaffordable_envelope_in_scenario": first_unaffordable,
            "first_provider_request_over_limit_in_scenario": first_over_provider_limit,
            "request_envelopes": envelopes, "batches": rows,
            "checker_capacity_forecast_envelopes": checker_envelopes,
            "checker_capacity_forecast": {
                "kind": "CONSERVATIVE_STRUCTURAL_HYPOTHESES_ALL_REJECT_NO_SEMANTIC_PREDICTIONS",
                "candidate_limit_per_event": MAX_CANDIDATES,
                "provider_calls": 0, "mock_checker_calls": len(checker_envelopes), "mock_retries": 0,
                "accepted_evidence": 0, "gold_labels_read": False, "f1_available": False,
                "estimated_checker_input_tokens": checker_total,
                "combined_primary_and_checker_input_estimate": combined_total,
                "combined_within_input_budget": combined_total <= budgets["max_input_tokens"],
                "conditional_provider_requests_without_retries": projected_calls,
                "conditional_provider_requests_with_one_retry_per_phase": projected_calls * 2,
                "conditional_requests_within_provider_budget": projected_calls <= budgets["max_provider_requests"],
                "retry_request_capacity_within_provider_budget": projected_calls * 2 <= budgets["max_provider_requests"],
                "combined_input_estimate_with_one_retry_per_phase": combined_total + retry_estimate,
                "retry_input_capacity_within_budget": combined_total + retry_estimate <= budgets["max_input_tokens"],
                "primary_output_capacity_guaranteed": False},
            "limitations": [
                "Local transport fixture rows do not assess architectural relations or measure F1.",
                "The negative scenario has no positive candidates and therefore no checker requests.",
                "Real positive candidates add checker envelopes; retries add requests and input tokens.",
                "The separate checker forecast uses fabricated hypotheses, not primary predictions or Gold links.",
                "Its maximum proof lists and up to 64 candidates can exceed feasible primary output capacity.",
                "Checker forecast estimates describe input capacity, never completeness of semantic judgment.",
                "Input estimates do not guarantee hosted completion, output capacity or provider price.",
                "The prepared 400000 input policy deliberately increases the historical 100000 compute budget.",
                "Protected source text has no citation handles; URLs and emails can also be screened.",
            ]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, help="Prepared v4.9 evaluation with pinned inputs")
    parser.add_argument("--decision", type=Path, help="Approved runtime S0; requires --history")
    parser.add_argument("--history", type=Path, help="Unlabeled canonical JSONL evidence")
    parser.add_argument("--model", default="gpt-6.1-sol", help="Opaque primary model ID; no provider call")
    parser.add_argument("--judge-model", default="gpt-6.1-sol", help="Opaque independent checker model ID")
    parser.add_argument("--nomination-mode", choices=("none",), default="none")
    for name, default in (("max-rounds", 6), ("max-queries", 12), ("max-reads", 36),
                          ("max-input-tokens", 400000), ("max-output-tokens", 16384),
                          ("max-provider-requests", 36)):
        parser.add_argument("--" + name, type=int, default=default)
    parser.add_argument("--output", type=Path, help="New JSON report; existing files are never overwritten")
    args = parser.parse_args()
    if args.evaluation is not None:
        if args.decision is not None or args.history is not None:
            parser.error("Choose --evaluation or both --decision and --history")
        evaluation = args.evaluation.resolve()
        config = json.loads((evaluation / "DEV_PREP_MANIFEST.json").read_text(encoding="utf-8"))
        if (config.get("kind") != KIND or config.get("investigation_profile") != PROFILE
                or config.get("nomination_mode") != "none"
                or config.get("gold_labels_in_agent_inputs") is not False):
            raise ValueError("Expected prepared unlabeled v4.9 event-pair-reviewed evaluation")
        from prepare_v49 import validate_prepared_configuration
        validate_prepared_configuration(config)
        decision_path, history_path = evaluation / "inputs" / DECISION_NAME, evaluation / "inputs" / HISTORY_NAME
        models, budgets = config["models"], {**config["budgets"], "max_output_tokens": args.max_output_tokens}
    else:
        if args.decision is None or args.history is None:
            parser.error("Provide --evaluation or both --decision and --history")
        decision_path, history_path = args.decision.resolve(), args.history.resolve()
        models = {"linker": args.model, "judge": args.judge_model}
        budgets = {name: getattr(args, name) for name in (
            "max_rounds", "max_queries", "max_reads", "max_input_tokens", "max_output_tokens", "max_provider_requests")}
    decision_bytes, history_bytes = decision_path.read_bytes(), history_path.read_bytes()
    if args.evaluation is not None and (
            _sha(decision_bytes) != config.get("runtime_s0_sha256")
            or _sha(history_bytes) != config.get("history_sha256")):
        raise ValueError("Prepared input digests do not match; no audit performed")
    report = audit_sources(json.loads(decision_bytes),
        [json.loads(line) for line in history_bytes.decode("utf-8").splitlines() if line.strip()], models, budgets,
        nomination_mode=args.nomination_mode)
    report["input_sha256"] = {"runtime_s0": _sha(decision_bytes), "history": _sha(history_bytes)}
    rendered = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        target = args.output.resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8") as output:
            output.write(rendered)
        print(json.dumps({"status": report["status"], "output": str(target),
                          "scenario_estimated_input_tokens": report["scenario_estimated_input_tokens"],
                          "scenario_within_nominal_estimate_budget": report["scenario_within_nominal_estimate_budget"]}, indent=2))


if __name__ == "__main__":
    main()
