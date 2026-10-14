"""Event request ceilings must match configured limits before paid calls."""
import json
from types import SimpleNamespace

import pytest

from evorationale.budget import Budget, BudgetExhausted
from evorationale import cli
from evorationale.event_agent import RequestBudgetTracker
from evorationale.event_context import select_event_batches
from evorationale.event_linking import EventLinker
from evorationale.memory import DecisionMemory
from evorationale.model import normalize_artifact


def test_output_guard_stops_before_input_charge_or_provider(approved_state):
    memory = DecisionMemory("budget-fixture", approved_state)
    tracker = RequestBudgetTracker(Budget(max_output_tokens=700), memory)
    with pytest.raises(BudgetExhausted, match="per_request_output_token_limit"):
        tracker({"model": "fixture", "max_output_tokens": 701})
    assert memory.token_count == 0 and tracker.requests == []


def test_linker_respects_smaller_configured_ceiling_on_retry(approved_state):
    source = normalize_artifact({
        "artifact_id": "change", "repository": approved_state["repository"],
        "source_type": "git_commit_diff_hunk", "source_location": "fixture://source",
        "title": "Design change", "timestamp": "2024-02-01T00:00:00Z",
        "content": "@@ -1 +1 @@\n-Previous mechanism.\n+Replacement mechanism.\n",
    })
    requests = []
    def respond(**request):
        requests.append(request)
        if len(requests) == 1:
            return SimpleNamespace(status="incomplete", output_text="")
        payload = json.loads(request["input"])
        ids = [e["id"] for e in payload["decision_state"]["elements"]]
        result = {"reviews": [{"artifact_handle": a["artifact_handle"],
            "considered_element_ids": ids, "status": "no_material_relation",
            "reason": "Synthetic completed transport fixture.", "links": []}
            for a in payload["artifacts"]]}
        return SimpleNamespace(status="completed", output_text=json.dumps(result))
    memory = DecisionMemory("budget-fixture", approved_state)
    tracker = RequestBudgetTracker(Budget(max_output_tokens=700), memory)
    linker = EventLinker("fixture", client=SimpleNamespace(responses=SimpleNamespace(create=respond)))
    batch = select_event_batches(approved_state, [source], 1)[0]
    assert linker.propose_event(approved_state, batch, charge=tracker) == []
    assert [r["max_output_tokens"] for r in requests] == [700, 700]
    assert tracker.summary()["max_output_tokens_per_request"] == 700
    assert tracker.summary()["provider_requests_reserved"] == 2


@pytest.mark.parametrize("limit,expected", [(None, 16384), (700, 700)])
def test_cli_event_output_limit_reaches_agent(tmp_path, monkeypatch, limit, expected):
    from evorationale import event_linking, event_verification
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-not-a-provider-key")
    monkeypatch.setattr(event_linking, "EventLinker", lambda model: SimpleNamespace(model=model))
    monkeypatch.setattr(event_verification, "EventSemanticJudge", lambda model: SimpleNamespace(model=model))
    args = SimpleNamespace(investigation_profile="event-complete", mode="api", backend="local",
        allow_repository_text_to_api=True, model="fixture-linker", judge_model="fixture-judge",
        memory="file", memory_dir=tmp_path, alloy_jar=None,
        max_rounds=6, max_queries=12, max_reads=36, max_input_tokens=100000,
        max_output_tokens=limit)
    agent = cli.build_agent(args)
    assert agent.budget.max_output_tokens == expected


def test_targeted_cli_does_not_claim_to_enforce_event_only_output_setting():
    with pytest.raises(RuntimeError, match="only by the event-complete profile"):
        cli.build_agent(SimpleNamespace(investigation_profile="targeted", max_output_tokens=700))
