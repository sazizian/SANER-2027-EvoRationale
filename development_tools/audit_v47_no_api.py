#!/usr/bin/env python3
"""Validate canonical source handles and both request envelopes without an API.

Only the runtime S0, unlabeled history and optional preparation manifest are
read. The local transport returns complete negative fixtures; it does not
assess semantics, produce evidence, or predict F1. The independent classifier
is exercised for every selected event without nomination requests by default.
The event-grounded profile permits no hosted nomination phase.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evorationale.budget import Budget
from evorationale.delta_context import build_delta_catalog
from evorationale.delta_linking import DeltaLinker, NoNomination
from evorationale.grounded_trace_verification import GroundedTraceSemanticJudge
from evorationale.diff_context import DIFF_SOURCE_TYPES, _lines
from evorationale.event_context import redact_event_source, select_event_batches
from evorationale.event_verification import _overlaps_sensitive_source
from evorationale.model import artifact_key, eligible, elements, normalize_history, validate_state
from evorationale.redaction import redact

DECISION_NAME = "S0_RETROSPECTIVE_RUNTIME.json"
HISTORY_NAME = "POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl"
_REASON = "LOCAL TRANSPORT FIXTURE ONLY: no architectural relation has been assessed."


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _without_terminator(raw: str) -> str:
    if raw.endswith("\r\n"):
        return raw[:-2]
    return raw[:-1] if raw[-1:] in "\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029" else raw


def _source_lines(source: dict[str, Any]) -> list[tuple[int, int, str, str]]:
    records = _lines(source)
    if source["source_type"] in DIFF_SOURCE_TYPES:
        if records is None:
            raise ValueError("Unparsable canonical diff source")
        return records
    result = []
    offset = 0
    for raw in source["content"].splitlines(keepends=True):
        result.append((offset, offset + len(raw), "statement", raw))
        offset += len(raw)
    return result


def _safe(source: dict[str, Any], text: str) -> bool:
    return bool(text) and redact(text, max_chars=len(text)) == text and not (
        _overlaps_sensitive_source(source["content"], text))


def validate_catalog(catalog: dict[str, Any], batch: list[dict[str, Any]]) -> dict[str, Any]:
    """Independently check outbound references against original source positions.

    Reports retain identities and counts, never raw source or protected text.
    The positional checks distinguish duplicate retained/changed occurrences.
    """
    artifacts = {f"A{i:04d}": source for i, source in enumerate(batch, 1)}
    if catalog["artifacts"] != artifacts:
        raise ValueError("Canonical artifact handle map differs from selected source versions")
    payload = catalog["payload"]
    context = payload["event_context"]
    if (catalog["context"]["artifact_keys"] != [artifact_key(source) for source in batch]
            or context["identity_sha256"] != catalog["context"]["identity_sha256"]
            or context["identity"] != catalog["context"]["identity"]):
        raise ValueError("Event context identity differs from selected source versions")
    if len(payload["artifacts"]) != len(batch) or len(context["canonical_artifacts"]) != len(batch):
        raise ValueError("Incomplete source catalog")
    source_entries = {entry["artifact_handle"]: entry for entry in context["canonical_artifacts"]}
    if len(source_entries) != len(batch) or set(source_entries) != set(artifacts):
        raise ValueError("Duplicate or unknown numbered-source artifact handle")
    seen_artifacts = set()
    seen_passages = set()
    seen_lines = set()
    changed_rows = []
    for row in payload["artifacts"]:
        handle = row["artifact_handle"]
        if handle not in artifacts or handle in seen_artifacts:
            raise ValueError("Duplicate or unknown artifact catalog handle")
        seen_artifacts.add(handle)
        source = artifacts[handle]
        if row["artifact_id"] != source["artifact_id"]:
            raise ValueError("Artifact catalog ID differs from canonical source version")
        entry = source_entries[handle]
        for name in ("artifact_id", "content_sha256"):
            expected = source[name]
            if entry[name] != expected:
                raise ValueError("Numbered-source identity differs from canonical source version")
        numbered = entry["numbered_source"].splitlines(keepends=True)
        reconstructed = ""
        for number, raw in enumerate(numbered, 1):
            prefix = f"{number}: "
            if not raw.startswith(prefix):
                raise ValueError("Invalid source-owned line numbering")
            reconstructed += raw[len(prefix):]
        if reconstructed != redact_event_source(source["content"]):
            raise ValueError("Numbered source does not reconstruct screened original source")
        physical = source["content"].splitlines(keepends=True)
        screened = reconstructed.splitlines(keepends=True)
        if len(physical) != len(screened):
            raise ValueError("Source screening changed physical line positions")
        records = _source_lines(source)
        screened_offsets = []
        screened_cursor = 0
        for raw in screened:
            screened_offsets.append(screened_cursor)
            screened_cursor += len(raw)
        positional_passages = []
        for suffix, coordinates in row["passages"].items():
            passage_handle = f"{handle}:{suffix}"
            if passage_handle in seen_passages or passage_handle not in catalog["passages"]:
                raise ValueError("Duplicate or unknown passage handle")
            seen_passages.add(passage_handle)
            passage = catalog["passages"][passage_handle]
            start, end, quote = passage["start"], passage["end"], passage["quote"]
            if (passage["artifact_handle"] != handle or not passage_handle.startswith(handle + ":P")
                    or type(start) is not int or type(end) is not int
                    or not 0 <= start < end <= len(source["content"])
                    or source["content"][start:end] != quote or len(quote) > 650
                    or not _safe(source, quote)):
                raise ValueError("Passage handle differs from safe exact canonical source span")
            if not isinstance(coordinates, list) or len(coordinates) != 4:
                raise ValueError("Malformed source-owned passage coordinates")
            first, last, first_column, last_column = coordinates
            if (any(type(n) is not int for n in (first, last, first_column, last_column))
                    or not 1 <= first <= last <= len(screened)
                    or not 0 <= first_column <= len(screened[first - 1])
                    or not 0 <= last_column <= len(screened[last - 1])):
                raise ValueError("Invalid source-owned passage line or column range")
            touched_lines = [i for i, (left, right, _role, _raw) in enumerate(records, 1)
                             if left < end and right > start]
            if (not touched_lines or (first, last) != (touched_lines[0], touched_lines[-1])
                    or first_column != len(redact_event_source(source["content"][:start])) - screened_offsets[first - 1]
                    or last_column != len(redact_event_source(source["content"][:end])) - screened_offsets[last - 1]):
                raise ValueError("Passage coordinates differ from exact original span occurrence")
            reconstructed_quote = (screened[first - 1][first_column:last_column] if first == last else
                                   screened[first - 1][first_column:] +
                                   "".join(screened[first:last - 1]) + screened[last - 1][:last_column])
            if reconstructed_quote != quote:
                raise ValueError("Passage columns do not reconstruct exact safe canonical quote")
            positional_passages.append((start, end))
        changed_handles = set()
        for reference_role, number in [(role, number) for role, numbers in row["line_roles"].items()
                                       for number in numbers]:
            if type(number) is not int or not 1 <= number <= len(records):
                raise ValueError("Invalid original source line position")
            line_handle = f"{handle}:L{number:04d}"
            if line_handle in seen_lines or line_handle not in catalog["lines"]:
                raise ValueError("Duplicate or unknown line handle")
            seen_lines.add(line_handle)
            left, _right, role, raw = records[number - 1]
            text = _without_terminator(raw)
            line = catalog["lines"][line_handle]
            if (line_handle != f"{handle}:L{number:04d}" or line["artifact_handle"] != handle
                    or reference_role != role or line["role"] != role
                    or role not in {"added", "removed", "unchanged", "statement"}
                    or line["start"] != left or line["end"] != left + len(text)
                    or line["text"] != text or source["content"][line["start"]:line["end"]] != text
                    or not _safe(source, text)):
                raise ValueError("Line handle differs from exact safe canonical position or mechanical role")
            if role in {"added", "removed"}:
                changed_handles.add(number)
        changed = [(i, left, _without_terminator(raw))
                   for i, (left, _right, role, raw) in enumerate(records, 1)
                   if role in {"added", "removed"}]
        safe_changed = [(i, left, text) for i, left, text in changed if _safe(source, text)]
        covered = [i for i, left, text in safe_changed
                   if any(start <= left and end >= left + len(text) for start, end in positional_passages)]
        if changed_handles != {i for i, _left, _text in safe_changed}:
            raise ValueError("Safe changed-line handles are missing or added")
        if len(covered) != len(safe_changed):
            raise ValueError("Safe changed lines lack exact contiguous passage coverage")
        expected_coverage = len(safe_changed) == len(changed)
        if changed and row["citation_coverage_complete"] != expected_coverage:
            raise ValueError("Citation completeness conceals unquotable changed source lines")
        if row["citation_coverage_complete"] != catalog["citation_coverage"][handle]:
            raise ValueError("Outbound citation completeness differs from canonical coverage")
        changed_rows.append({"artifact_id": source["artifact_id"], "artifact_key": artifact_key(source),
                             "changed_source_lines": len(changed),
                             "safe_changed_source_lines": len(safe_changed),
                             "safe_changed_line_handles_checked": len(changed_handles),
                             "covered_safe_changed_source_lines": len(covered),
                             "unquotable_changed_source_lines": len(changed) - len(safe_changed)})
    if seen_passages != set(catalog["passages"]) or seen_lines != set(catalog["lines"]):
        raise ValueError("Local canonical references are absent from outbound catalog")
    return {"numbered_source_reconstructions_checked": len(source_entries),
            "exact_passage_handles_checked": len(seen_passages),
            "exact_line_handles_and_roles_checked": len(seen_lines),
            "changed_line_coverage": changed_rows}


class _FakeResponses:
    """Explicit local transport: no SDK, network, credentials, or positive links."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

    def create(self, **request: Any) -> SimpleNamespace:
        self.requests.append(deepcopy(request))
        payload = json.loads(request["input"])
        stage = request["text"]["format"]["name"]
        considered = [element["id"] for element in payload["fixed_s0"]["elements"]]
        review_fields = {"element_ids": []} if stage == "fixed_s0_delta_target_nomination" else {"links": []}
        result = {"considered_element_ids": considered,
                  "reviews": [{"artifact_handle": artifact["artifact_handle"],
                               "status": "no_material_relation", "reason": _REASON,
                               **({"support_reason": _REASON, "change_reason": _REASON}
                                  if stage != "fixed_s0_delta_target_nomination" else {}), **review_fields}
                              for artifact in payload["artifacts"]]}
        return SimpleNamespace(status="completed", output_text=json.dumps(result))


def audit_sources(state_input: dict[str, Any], history_input: list[dict[str, Any]],
                  models: dict[str, str], budgets: dict[str, int], *,
                  nomination_mode: str = "none") -> dict[str, Any]:
    """Forecast complete negative transport fixtures without charging a real run."""
    if (not isinstance(models, dict) or set(models) != {"linker", "judge"}
            or any(not isinstance(v, str) or not v.strip() for v in models.values())):
        raise ValueError("Expected explicit opaque linker and judge model IDs")
    names = ("max_rounds", "max_queries", "max_reads", "max_input_tokens")
    if (not isinstance(budgets, dict)
            or any(type(budgets.get(n)) is not int or budgets[n] < 1 for n in names)):
        raise ValueError("Expected positive integer evaluation budgets")
    output_limit = budgets.get("max_output_tokens", 16384)
    if type(output_limit) is not int or output_limit < 1:
        raise ValueError("Expected positive integer output-token budget")
    if nomination_mode != "none":
        raise ValueError("The event-grounded profile requires nomination mode none")
    original_inputs = deepcopy((state_input, history_input))
    state = validate_state(state_input)
    history = normalize_history(history_input)
    allowed = [artifact for artifact in history if eligible(state, artifact)]
    selected = select_event_batches(state, history, budgets["max_reads"])
    active = selected[:min(budgets["max_rounds"], budgets["max_queries"])]
    fake = _FakeResponses()
    client = SimpleNamespace(responses=fake)
    linker = (DeltaLinker(models["linker"], client=client) if nomination_mode == "model"
              else NoNomination())
    judge = GroundedTraceSemanticJudge(models["judge"], client=client)
    # Supply the configured per-request ceiling without enforcing the cumulative
    # estimate: a forecast must expose a complete oversize scenario transparently.
    def forecast_only(_request: Any) -> None:
        pass
    forecast_only.budget = SimpleNamespace(max_output_tokens=output_limit)
    envelopes = []
    rows = []
    cumulative = 0
    first_unaffordable = None
    reviewed_keys = set()
    for number, batch in enumerate(active, 1):
        catalog = build_delta_catalog(state, batch)
        checks = validate_catalog(catalog, batch)
        before = len(fake.requests)
        nominees = linker.propose_event(state, batch, charge=forecast_only)
        if nominees:
            raise AssertionError("Negative transport fixture unexpectedly nominated an element")
        accepted, rejected = judge.review_event(state, batch, nominees, charge=forecast_only)
        if accepted or rejected:
            raise AssertionError("Negative transport fixture produced source evidence or rejection")
        requests = fake.requests[before:]
        expected_stages = ["linker", "judge"] if nomination_mode == "model" else ["judge"]
        if len(requests) != len(expected_stages):
            raise AssertionError("Expected independent request count differs from nomination mode")
        totals = {}
        for request in requests:
            stage = ("linker" if request["text"]["format"]["name"] == "fixed_s0_delta_target_nomination"
                     else "judge")
            expected_payload = (catalog["payload"] if stage == "judge" else {
                "fixed_s0": catalog["payload"]["fixed_s0"],
                "event_context": catalog["payload"]["event_context"],
                "artifacts": [{"artifact_handle": handle,
                               "citation_coverage_complete": catalog["citation_coverage"][handle]}
                              for handle in catalog["artifacts"]],
            })
            if json.loads(request["input"]) != expected_payload:
                raise ValueError("Actual request source payload differs from validated canonical catalog")
            estimate = Budget.estimate_tokens(request)
            cumulative += estimate
            if first_unaffordable is None and cumulative > budgets["max_input_tokens"]:
                first_unaffordable = {"batch": number, "stage": stage,
                                      "cumulative_estimated_input_tokens": cumulative}
            envelopes.append({"batch": number, "stage": stage,
                              "estimated_input_tokens": estimate,
                              "cumulative_estimated_input_tokens": cumulative,
                              "max_output_tokens": request["max_output_tokens"],
                              "model": request["model"],
                              "request_sha256": _sha(json.dumps(request, sort_keys=True,
                                                                ensure_ascii=False).encode("utf-8")),
                              "includes_full_schema_and_instructions": True,
                              "mock_response_received": True})
            totals[stage] = estimate
        if list(totals) != expected_stages:
            raise AssertionError("Independent classifier request missing or unexpected nomination request")
        reviewed_keys.update(artifact_key(artifact) for artifact in batch)
        element_ids = {element["id"] for element in elements(state)}
        reviews = linker.last_reviews + judge.last_reviews
        if len(reviews) != len(expected_stages) * len(batch) or not all(
                set(review["considered_element_ids"]) == element_ids for review in reviews):
            raise ValueError("Incomplete mocked fixed-S0 artifact reviews")
        rows.append({"batch": number, "artifact_ids": [artifact["artifact_id"] for artifact in batch],
                     "artifact_versions": len(batch), "source_bytes": catalog["context"]["source_bytes"],
                     "event_context_complete": catalog["context"]["complete"],
                     "synthetic_nominations": 0, "independent_judge_called_with_empty_nominations": True,
                     "all_source_artifacts_visible": len(catalog["payload"]["artifacts"]) == len(batch),
                     "all_s0_elements_considered_by_mock_judge": True,
                     "nomination_model_review_performed": nomination_mode == "model",
                     "all_s0_elements_considered_by_both_mock_stages": nomination_mode == "model",
                     "all_outbound_citation_coverage_complete": all(catalog["citation_coverage"].values()),
                     "incomplete_outbound_citation_artifact_ids": [catalog["artifacts"][handle]["artifact_id"]
                         for handle, complete in catalog["citation_coverage"].items() if not complete],
                     "request_envelope_estimates": totals, **checks})
    if (state_input, history_input) != original_inputs:
        raise AssertionError("Source-only audit mutated supplied inputs")
    return {"status": "V47_SOURCE_ONLY_SYNTHETIC_PREFLIGHT_COMPLETED_NO_API_CALLED",
            "investigation_profile": "event-grounded", "nomination_mode": nomination_mode,
            "semantic_result_available": False,
            "gold_labels_read": False, "provider_calls": 0, "mock_transport_calls": len(fake.requests),
            "mock_nomination_requests": sum(request["stage"] == "linker" for request in envelopes),
            "mock_independent_classifier_requests": sum(request["stage"] == "judge" for request in envelopes),
            "approval_mode": "APPROVED_RUNTIME_INPUT_REQUIRED",
            "input_human_approved": state_input.get("human_approved"), "state_approval_changed": False,
            "scenario": ("COMPLETE_NEGATIVE_MOCK_REVIEWS_BOTH_STAGES_EMPTY_NOMINATIONS_NO_RETRIES"
                         if nomination_mode == "model" else
                         "COMPLETE_NEGATIVE_MOCK_INDEPENDENT_REVIEWS_NO_NOMINATION_REQUESTS_NO_RETRIES"),
            "budget_estimator": "FULL_REQUEST_ENVELOPE_UTF8_ESTIMATE_NOT_PROVIDER_TOKENIZER_OR_PRICE",
            "models": models, "nominal_budgets": budgets,
            "max_output_tokens_per_request": output_limit,
            "eligible_artifact_versions": len(allowed), "selected_batches": len(selected),
            "round_and_query_bounded_batches": len(active),
            "structurally_reviewable_artifact_versions": len(reviewed_keys),
            "structurally_reviewable_diff_versions": sum(artifact["source_type"] in DIFF_SOURCE_TYPES
                and artifact_key(artifact) in reviewed_keys for artifact in allowed),
            "outside_round_query_read_selection_ids": [artifact["artifact_id"] for artifact in allowed
                                                      if artifact_key(artifact) not in reviewed_keys],
            "scenario_estimated_input_tokens": cumulative,
            "scenario_within_nominal_estimate_budget": cumulative <= budgets["max_input_tokens"],
            "first_unaffordable_envelope_in_scenario": first_unaffordable,
            "request_envelopes": envelopes, "batches": rows,
            "limitations": [
                "Local transport fixtures do not assess architectural relations or measure F1.",
                "Real outputs, provider tokenization and retries may differ from this no-retry scenario.",
                "Input estimates below a configured limit do not guarantee hosted completion or price.",
                "Negative fake replies do not exercise positive-link output size or semantic validation.",
                "Protected source text has no citation handles; URLs and emails can also be screened.",
            ]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, help="Prepared v4.7 evaluation with pinned inputs")
    parser.add_argument("--decision", type=Path, help="Approved runtime S0; requires --history")
    parser.add_argument("--history", type=Path, help="Unlabeled canonical JSONL evidence")
    parser.add_argument("--model", default="gpt-6.1-sol", help="Opaque proposer model ID; no provider call")
    parser.add_argument("--judge-model", default="gpt-6.1-sol", help="Opaque independent model ID")
    parser.add_argument("--nomination-mode", choices=("none",), default="none",
                        help="Independent classifier only; no hosted nomination phase")
    parser.add_argument("--max-rounds", type=int, default=6)
    parser.add_argument("--max-queries", type=int, default=12)
    parser.add_argument("--max-reads", type=int, default=36)
    parser.add_argument("--max-input-tokens", type=int, default=100000)
    parser.add_argument("--max-output-tokens", type=int, default=16384)
    parser.add_argument("--output", type=Path, help="New JSON report; existing files are never overwritten")
    args = parser.parse_args()
    if args.evaluation is not None:
        if args.decision is not None or args.history is not None:
            parser.error("Choose --evaluation or both --decision and --history")
        evaluation = args.evaluation.resolve()
        config = json.loads((evaluation / "DEV_PREP_MANIFEST.json").read_text(encoding="utf-8"))
        if (config.get("kind") != "DEVELOPMENT_ONLY_V47_EVENT_GROUNDED_COMPARISON"
                or config.get("investigation_profile") != "event-grounded"
                or config.get("nomination_mode") != "none"
                or config.get("gold_labels_in_agent_inputs") is not False):
            raise ValueError("Expected prepared unlabeled v4.7 event-grounded evaluation")
        decision_path, history_path = evaluation / "inputs" / DECISION_NAME, evaluation / "inputs" / HISTORY_NAME
        models, budgets = config["models"], {**config["budgets"], "max_output_tokens": args.max_output_tokens}
    else:
        if args.decision is None or args.history is None:
            parser.error("Provide --evaluation or both --decision and --history")
        decision_path, history_path = args.decision.resolve(), args.history.resolve()
        models = {"linker": args.model, "judge": args.judge_model}
        budgets = {name: getattr(args, name) for name in (
            "max_rounds", "max_queries", "max_reads", "max_input_tokens", "max_output_tokens")}
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
