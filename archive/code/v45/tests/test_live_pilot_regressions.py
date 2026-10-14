"""Regressions added after the Azure AVNM model-assisted pilot of 2026-10-10."""
import json
from types import SimpleNamespace

import pytest

from evorationale.agent import EvoRationaleAgent
from evorationale.budget import Budget
from evorationale.linking import candidate_link
from evorationale.memory import DecisionMemory
from evorationale.model import element_by_id
from evorationale.planning import TemporalQueryPlanner
from evorationale.structured_json import StructuredModelResponseError, request_json_object
from evorationale.verification import EvidenceVerifier, OpenAISemanticJudge

SCHEMA = {'type': 'object', 'properties': {'ok': {'type': 'boolean'}},
          'required': ['ok'], 'additionalProperties': False}


def call(client):
    return request_json_object(client=client, model='mock-model', name='bounded_json',
                               schema=SCHEMA, instructions='Return JSON', payload={'x': 1},
                               initial_output_tokens=600, attempts=2)


def test_empty_first_response_uses_bounded_retry():
    class Responses:
        def __init__(self): self.budgets = []
        def create(self, **kwargs):
            self.budgets.append(kwargs['max_output_tokens'])
            if len(self.budgets) == 1:
                return SimpleNamespace(status='incomplete', output_text='')
            return SimpleNamespace(status='completed', output_text='{"ok": true}')
    fake = Responses()
    assert call(SimpleNamespace(responses=fake)) == {'ok': True}
    assert fake.budgets == [600, 1200]


def test_two_invalid_json_responses_fail_closed():
    class Responses:
        def __init__(self): self.calls = 0
        def create(self, **kwargs):
            self.calls += 1
            return SimpleNamespace(status='completed', output_text='')
    fake = Responses()
    with pytest.raises(StructuredModelResponseError, match='missing_output_text'):
        call(SimpleNamespace(responses=fake))
    assert fake.calls == 2


def test_structured_judge_retries_then_accepts_only_supported_boolean():
    class Responses:
        def __init__(self): self.calls = 0
        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return SimpleNamespace(status='incomplete', output_text='')
            return SimpleNamespace(status='completed', output_text=json.dumps({'supported': True, 'reason': 'direct'}))
    fake = Responses()
    judge = OpenAISemanticJudge('mock', client=SimpleNamespace(responses=fake))
    assert judge.supports({'id': 'A1', 'text': 'Profile updates infrequent'},
                          'Profile update tests support that profile updates remain infrequent', 'supports') == (True, 'MODEL_ASSESSED:direct')
    assert fake.calls == 2


def test_semantic_judge_exhaustion_rejects_link_not_invents(approved_state, history):
    class Empty:
        def create(self, **kwargs): return SimpleNamespace(status='incomplete', output_text='')
    judge = OpenAISemanticJudge('mock', client=SimpleNamespace(responses=Empty()))
    a = next(x for x in history if x['artifact_id'] == 'inc-017')
    link = candidate_link(a, element_by_id(approved_state)['A1'], 'contradicts', a['content'], 0.75)
    passed, rejected = EvidenceVerifier(judge).verify(approved_state, history, [link])
    assert passed == []
    assert rejected[0]['reasons'] == ['semantic_judge_error:response_incomplete']


def test_untouched_required_need_gets_turn_before_repeated_retry(approved_state):
    planner = TemporalQueryPlanner()
    memory = DecisionMemory(run_id='test', initial_state=approved_state,
                            needs=planner.initialize(approved_state), round_count=1)
    a1 = next(x for x in memory.needs if x['id'] == 'need:A1')
    e1 = next(x for x in memory.needs if x['id'] == 'need:E1')
    a1['attempts'] = 1
    memory.verifier_feedback.append({'element_id': 'A1', 'reasons': ['semantic_judge_error:response_incomplete']})
    assert e1['attempts'] == 0
    question = planner.select(approved_state, memory)
    assert question['id'] == 'need:E1'


def test_incomplete_with_supported_claim_does_not_mark_claim_unsupported(approved_state, history):
    a = next(x for x in history if x['artifact_id'] == 'inc-017')
    class SingleLinker:
        def propose(self, state, artifacts, question):
            matches = [x for x in artifacts if x['artifact_id'] == a['artifact_id']]
            if not matches: return []
            return [candidate_link(matches[0], element_by_id(state)['A1'], 'contradicts',
                                   matches[0]['content'], 0.8, question['id'])]
    report = EvoRationaleAgent(linker=SingleLinker(), budget=Budget(max_rounds=2)).run(approved_state, [a]).report
    assert report['recommended_outcome'] == 'REVALIDATE'
    assert report['verification']['status'] == 'UNRESOLVED'
    assert report['verification']['investigation_complete'] is False
    assert report['verification']['claim_count'] == 1
    assert report['unsupported_claim_rate'] == 0.0
