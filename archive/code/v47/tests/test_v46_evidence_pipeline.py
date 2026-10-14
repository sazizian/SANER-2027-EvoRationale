"""Source-only integration contracts for the optional evidence-trace profile.

Controlled semantic replies exercise request boundaries, honest partial coverage,
source provenance, budgets and non-overwrite behavior. They do not measure a
hosted model's ability to choose the right architectural relation.
"""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from evorationale import cli
from evorationale.agent import EvoRationaleAgent
from evorationale.budget import Budget
from evorationale.delta_context import build_delta_catalog
from evorationale.delta_linking import NoNomination
from evorationale.event_agent import EventReviewAgent
from evorationale.event_context import select_event_batches
from evorationale.model import artifact_key, element_by_id, normalize_artifact
from test_v45_delta_verification import case, effect


DOCUMENTATION = ("@@ -1 +1 @@\n-Queue runtime notes.\n"
                 "+Approved orders are persisted through CentralQueue.\n")


class Provider:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def create(self, **request):
        self.calls.append(deepcopy(request))
        return SimpleNamespace(status="completed", output_text=json.dumps(self.reply),
                               usage={"input_tokens": 151, "output_tokens": 37, "total_tokens": 188})


def reviewer(provider):
    from evorationale.evidence_trace_verification import EvidenceTraceSemanticJudge
    return EvidenceTraceSemanticJudge("synthetic-independent-reviewer",
                                      client=SimpleNamespace(responses=provider))


def reply(state, catalog, effects=None):
    effects = effects or {}
    positive = {"none", "invariant", "implementation_only", "uncertain"}
    return {"considered_element_ids": list(element_by_id(state)), "reviews": [
        {"artifact_handle": handle,
         "status": "relation_found" if any(link["change_kind"] not in positive
                                            for link in effects.get(handle, [])) else "no_material_relation",
         "reason": "Independently assessed every fixed target against this exact source.",
         "support_reason": "Assessed current qualified evidence independently of novelty of the underlying design.",
         "change_reason": "Assessed adverse architectural effects independently of documentary corroboration.",
         "links": effects.get(handle, [])} for handle in catalog["artifacts"]]}


def support(state, catalog, handle="A0001", **changes):
    fields = dict(before_claim="The earlier line supplies no statement about persistence.",
                  after_claim="The added statement documents persistence of approved orders through CentralQueue.",
                  change_kind="documented_support", evidence_basis="adopted_design_statement",
                  effect_basis="current_design_statement",
                  local_contribution="The added line explicitly names the target's persistence authority.",
                  current_claim_entailed=True, context_establishes_replacement=False,
                  replacement_is_explicit=False, material_target_delta=False,
                  qualification="Documentary support for the specified persistence mechanism; no deployed observation.")
    fields.update(changes)
    return effect(state, catalog, handle=handle, **fields)


def configured_args(tmp_path, **changes):
    values = dict(investigation_profile="event-evidence", max_output_tokens=None,
                  delta_nomination="none", max_rounds=6, max_queries=12, max_reads=36,
                  max_input_tokens=100000, mode="api", backend="local",
                  allow_repository_text_to_api=True, model="opaque-unused-linker-field",
                  judge_model="opaque-independent-classifier", memory="file",
                  memory_dir=tmp_path / "memory", alloy_jar="", embedding_revision="")
    values.update(changes)
    return SimpleNamespace(**values)


def test_opt_in_evidence_dispatch_uses_only_independent_classifier(monkeypatch, tmp_path):
    from evorationale import evidence_trace_verification, delta_linking
    seen = []
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unused-key")
    monkeypatch.setattr(delta_linking, "DeltaLinker", lambda *args, **kw: pytest.fail("Unexpected hosted nomination"))
    monkeypatch.setattr(evidence_trace_verification, "EvidenceTraceSemanticJudge",
                        lambda model: seen.append(model) or object())
    agent = cli.build_agent(configured_args(tmp_path, max_output_tokens=8096))
    assert seen == ["opaque-independent-classifier"]
    assert isinstance(agent.linker, NoNomination)
    assert agent.profile == "event-evidence"
    assert agent.budget.max_output_tokens == 8096
    assert agent.budget.max_rounds == 6 and agent.budget.max_queries == 12
    assert agent.budget.max_artifact_reads == 36 and agent.budget.max_input_tokens == 100000


def test_default_targeted_profile_remains_offline_and_unchanged(monkeypatch, tmp_path):
    from evorationale import evidence_trace_verification
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(evidence_trace_verification, "EvidenceTraceSemanticJudge",
                        lambda *args, **kw: pytest.fail("Opt-in classifier used by default"))
    args = configured_args(tmp_path, mode="offline")
    del args.investigation_profile
    agent = cli.build_agent(args)
    assert isinstance(agent, EvoRationaleAgent)
    assert agent.budget.max_output_tokens == 4096


@pytest.mark.parametrize("profile", ["event-complete", "event-delta"])
def test_legacy_event_profiles_preserve_their_judges(monkeypatch, tmp_path, profile):
    from evorationale import event_linking, event_verification, delta_verification, evidence_trace_verification
    event_judge, delta_judge, event_linker = object(), object(), object()
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unused-key")
    monkeypatch.setattr(event_linking, "EventLinker", lambda model: event_linker)
    monkeypatch.setattr(event_verification, "EventSemanticJudge", lambda model: event_judge)
    monkeypatch.setattr(delta_verification, "DeltaSemanticJudge", lambda model: delta_judge)
    monkeypatch.setattr(evidence_trace_verification, "EvidenceTraceSemanticJudge",
                        lambda *args, **kw: pytest.fail("New classifier used by legacy profile"))
    agent = cli.build_agent(configured_args(tmp_path, investigation_profile=profile))
    assert agent.profile == profile
    assert agent.judge is (event_judge if profile == "event-complete" else delta_judge)
    assert agent.linker is event_linker if profile == "event-complete" else isinstance(agent.linker, NoNomination)


def test_requests_have_every_exact_fixed_target_and_no_reference_or_nomination_data(approved_state):
    state, batch = case(approved_state, DOCUMENTATION)
    state["gold_labels"] = {"DELTA_TARGET": "SYNTHETIC_REFERENCE_MUST_NOT_REACH_MODEL"}
    state["evaluation_metadata"] = "SYNTHETIC_REFERENCE_MUST_NOT_REACH_MODEL"
    catalog = build_delta_catalog(state, batch)
    provider = Provider(reply(state, catalog))
    nomination = [{"artifact_key": artifact_key(batch[0]), "artifact_id": batch[0]["artifact_id"],
                   "decision_element_id": "DELTA_TARGET"}]
    accepted, feedback = reviewer(provider).review_event(state, batch, nomination)
    assert not accepted and not feedback and len(provider.calls) == 1
    payload = json.loads(provider.calls[0]["input"])
    assert {x["id"]: x["text"] for x in payload["fixed_s0"]["elements"]} == {
        key: value["text"] for key, value in element_by_id(state).items()}
    assert "SYNTHETIC_REFERENCE_MUST_NOT_REACH_MODEL" not in provider.calls[0]["input"]
    assert "gold_labels" not in payload and "evaluation_metadata" not in payload
    assert "nominees" not in payload and "proposals" not in payload


def test_documentary_support_is_partial_and_never_resolves_whole_need(approved_state):
    state, batch = case(approved_state, DOCUMENTATION)
    state["central_element_ids"] = ["DELTA_TARGET"]
    catalog = build_delta_catalog(state, batch)
    provider = Provider(reply(state, catalog, {"A0001": [support(state, catalog)]}))
    run = EventReviewAgent(linker=NoNomination(), judge=reviewer(provider), profile="event-evidence",
                          budget=Budget(max_rounds=1, max_artifact_reads=1,
                                        max_input_tokens=100000, max_output_tokens=16384)).run(state, batch)
    assert len(provider.calls) == len(run.memory.verified_links) == 1
    link = run.memory.verified_links[0]
    assert link["relation"] == "supports" and link["quote"] in batch[0]["content"]
    assert link["semantic_assessment"]["whole_element_supported"] is False
    assert link["semantic_assessment"]["architectural_change"] is False
    assert link["semantic_assessment"]["deployed_behavior_verified"] is False
    assert link["semantic_assessment"]["claim_scope"] == "material_subclaim"
    need = next(n for n in run.memory.needs if n["element_id"] == "DELTA_TARGET")
    assert need["status"] == "PARTIAL_EVIDENCE"
    assert run.report["verification"]["status"] == "UNRESOLVED"
    assert run.report["investigation_profile"] == "event-evidence"
    assert run.report["nomination_mode"] == "none"
    assert run.report["budget_usage"]["provider_requests_reserved"] == 1
    assert run.report["budget_usage"]["provider_reported_input_tokens"] == 151
    assert run.report["investigation_coverage"]["nomination_review_records"] == []
    record = run.report["investigation_coverage"]["artifact_review_records"][0]
    assert record["support_reason"] and record["change_reason"]


def test_current_support_and_migration_effect_can_both_be_recorded(approved_state):
    state, first = case(approved_state, DOCUMENTATION)
    first[0].update(source_commit_sha="a" * 40, source_file="orders.md")
    raw = deepcopy(first[0])
    raw.update(artifact_id="synthetic-worker-migration",
               content="@@ -1 +1 @@\n-Worker persists approved orders through CentralQueue.\n"
                       "+Worker persists approved orders through LocalLedger.\n")
    raw.pop("content_sha256", None)
    raw.pop("version_id", None)
    second = normalize_artifact(raw)
    batch = select_event_batches(state, [first[0], second], 2)[0]
    catalog = build_delta_catalog(state, batch)
    doc_handle = next(key for key, a in catalog["artifacts"].items() if a["artifact_id"] == first[0]["artifact_id"])
    migration_handle = next(key for key, a in catalog["artifacts"].items() if a["artifact_id"] == second["artifact_id"])
    migration = effect(state, catalog, handle=migration_handle, effect_basis="direct_delta",
                       local_contribution="Worker's local persistence authority is replaced.",
                       current_claim_entailed=False, context_establishes_replacement=False)
    provider = Provider(reply(state, catalog, {doc_handle: [support(state, catalog, handle=doc_handle)], migration_handle: [migration]}))
    run = EventReviewAgent(linker=NoNomination(), judge=reviewer(provider), profile="event-evidence").run(state, batch)
    assert {x["relation"] for x in run.memory.verified_links} == {"supports", "supersedes"}
    need = next(n for n in run.memory.needs if n["element_id"] == "DELTA_TARGET")
    assert need["status"] == "CONFLICTING_EVIDENCE"
    assert run.report["verification"]["status"] == "UNRESOLVED"


def test_dependent_migration_retains_local_and_context_source_handles(approved_state):
    state, batch = case(approved_state)
    batch[0].update(source_commit_sha="a" * 40, source_file="orders.md")
    raw = deepcopy(batch[0])
    raw.update(artifact_id="synthetic-client-migration",
               content="@@ -1 +1 @@\n-Client submits approved orders to CentralQueue.\n"
                       "+Client submits approved orders to LocalLedger.\n")
    raw.pop("content_sha256", None)
    raw.pop("version_id", None)
    batch.append(normalize_artifact(raw))
    batch = select_event_batches(state, batch, 2)[0]
    catalog = build_delta_catalog(state, batch)
    producer = next(key for key, a in catalog["artifacts"].items() if a["artifact_id"] == "synthetic-order-change")
    consumer = next(key for key, a in catalog["artifacts"].items() if a["artifact_id"] == "synthetic-client-migration")
    context_handles = [key for key, value in catalog["lines"].items()
                       if value["artifact_handle"] == producer and value["role"] == "added"]
    migration = effect(state, catalog, handle=consumer, change_kind="dependent_replacement",
                       effect_basis="dependent_migration", context_line_handles=context_handles,
                       local_contribution="The consumer changes its destination alongside the same-event chosen authority migration.",
                       current_claim_entailed=False, context_establishes_replacement=True)
    provider = Provider(reply(state, catalog, {consumer: [migration]}))
    run = EventReviewAgent(linker=NoNomination(), judge=reviewer(provider), profile="event-evidence").run(state, batch)
    assert len(run.memory.verified_links) == 1 and not run.memory.verifier_feedback
    link = run.memory.verified_links[0]
    assessed = link["semantic_assessment"]
    assert link["artifact_id"] == "synthetic-client-migration" and link["relation"] == "supersedes"
    assert assessed["effect_basis"] == "dependent_migration"
    assert assessed["context_line_handles"] == context_handles
    assert all(key.startswith(consumer + ":") for key in assessed["before_line_handles"] + assessed["after_line_handles"])
    assert assessed["exact_context_source_lines"] == [catalog["lines"][key]["text"] for key in context_handles]
    assert assessed["canonical_content_sha256"] == catalog["artifacts"][consumer]["content_sha256"]


@pytest.mark.parametrize("malformed", [False, True])
def test_semantic_abstention_is_distinct_from_technical_coverage_failure(approved_state, malformed):
    state, batch = case(approved_state, DOCUMENTATION)
    catalog = build_delta_catalog(state, batch)
    output = reply(state, catalog)
    if malformed:
        output["considered_element_ids"].pop()
    provider = Provider(output)
    run = EventReviewAgent(linker=NoNomination(), judge=reviewer(provider), profile="event-evidence").run(state, batch)
    assert not run.memory.verified_links and not run.memory.rejected_interpretations
    coverage = run.report["investigation_coverage"]
    if malformed:
        assert run.memory.technical_verification_failures
        assert coverage["model_reported_reviewed_artifact_versions"] == 0
        assert coverage["not_semantically_reviewed_artifact_ids"] == [batch[0]["artifact_id"]]
    else:
        assert not run.memory.technical_verification_failures
        assert coverage["model_reported_reviewed_artifact_versions"] == 1
        assert coverage["not_semantically_reviewed_artifact_ids"] == []
        assert coverage["artifact_review_records"][0]["status"] == "no_material_relation"


def test_unentailed_support_is_semantic_rejection_with_source_coverage(approved_state):
    state, batch = case(approved_state, DOCUMENTATION)
    catalog = build_delta_catalog(state, batch)
    provider = Provider(reply(state, catalog, {"A0001": [support(state, catalog, current_claim_entailed=False)]}))
    run = EventReviewAgent(linker=NoNomination(), judge=reviewer(provider), profile="event-evidence").run(state, batch)
    assert not run.memory.verified_links and run.memory.rejected_interpretations
    assert not run.memory.technical_verification_failures
    assert run.report["investigation_coverage"]["model_reported_reviewed_artifact_versions"] == 1


def test_input_budget_is_reserved_before_any_provider_call(approved_state):
    state, batch = case(approved_state, DOCUMENTATION)
    catalog = build_delta_catalog(state, batch)
    provider = Provider(reply(state, catalog, {"A0001": [support(state, catalog)]}))
    run = EventReviewAgent(linker=NoNomination(), judge=reviewer(provider), profile="event-evidence",
                          budget=Budget(max_input_tokens=1, max_output_tokens=16384)).run(state, batch)
    assert provider.calls == [] and not run.memory.verified_links
    assert run.report["verification"]["status"] == "UNRESOLVED"
    assert run.report["budget_usage"]["provider_requests_reserved"] == 0
    assert "token" in run.report["stopping_reason"]


@pytest.mark.parametrize("existing", ["report.json", "trace.json", "data_audit.json", "manifest.json"])
def test_evidence_cli_preserves_previous_run_before_classifier_construction(approved_state, tmp_path, monkeypatch, existing):
    state, batch = case(approved_state, DOCUMENTATION)
    decision, history, output = tmp_path / "state.json", tmp_path / "history.jsonl", tmp_path / "run"
    decision.write_text(json.dumps(state))
    history.write_text("".join(json.dumps(item) + "\n" for item in batch))
    output.mkdir()
    sentinel = b"preserved previous experiment bytes\n"
    (output / existing).write_bytes(sentinel)
    monkeypatch.setattr(cli, "build_agent", lambda *args: pytest.fail("Provider constructed before non-overwrite preflight"))
    args = configured_args(tmp_path, decision=decision, history=history, output=output)
    with pytest.raises(FileExistsError, match="already contains experiment files"):
        cli._run(args)
    assert (output / existing).read_bytes() == sentinel
