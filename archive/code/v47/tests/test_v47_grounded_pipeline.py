"""Single-phase grounded profile, complete coverage and honest partial outcomes."""
from types import SimpleNamespace

from evorationale import cli
from evorationale.budget import Budget
from evorationale.delta_context import build_delta_catalog
from evorationale.delta_linking import NoNomination
from evorationale.event_agent import EventReviewAgent
from evorationale.grounded_trace_verification import GroundedTraceSemanticJudge
from test_v46_evidence_pipeline import Provider, DOCUMENTATION, case, configured_args, reply, support


def test_cli_dispatches_grounded_profile_without_nomination(monkeypatch, tmp_path):
    from evorationale import grounded_trace_verification
    seen = []
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-unused-key')
    monkeypatch.setattr(grounded_trace_verification, 'GroundedTraceSemanticJudge',
                        lambda model: seen.append(model) or object())
    agent = cli.build_agent(configured_args(tmp_path, investigation_profile='event-grounded'))
    assert agent.profile == 'event-grounded' and isinstance(agent.linker, NoNomination)
    assert seen == ['opaque-independent-classifier']


def test_grounded_pipeline_records_predicate_proof_and_partial_need(approved_state):
    state, batch = case(approved_state, DOCUMENTATION)
    state['central_element_ids'] = ['DELTA_TARGET']
    catalog = build_delta_catalog(state,batch)
    item = support(state, catalog, target_contribution='direct_predicate_evidence',
                   predicate_line_handles=[h for h,l in catalog['lines'].items() if l['role']=='added'])
    provider = Provider(reply(state,catalog,{'A0001':[item]}))
    judge = GroundedTraceSemanticJudge('fixture',client=SimpleNamespace(responses=provider))
    result = EventReviewAgent(linker=NoNomination(),judge=judge,profile='event-grounded',
        budget=Budget(max_rounds=1,max_artifact_reads=1,max_input_tokens=100000,max_output_tokens=16384)).run(state,batch)
    assert len(provider.calls)==len(result.memory.verified_links)==1
    assert result.report['nomination_mode']=='none' and result.report['investigation_profile']=='event-grounded'
    assert result.report['verification']['status']=='UNRESOLVED'
    assert 'Predicate contributions' in result.report['investigation_coverage']['classification_policy']
    assert any(n['status']=='PARTIAL_EVIDENCE' for n in result.memory.needs if n['element_id']=='DELTA_TARGET')


def test_grounded_predicate_rejection_is_semantic_not_transport_failure(approved_state):
    state,batch=case(approved_state,DOCUMENTATION)
    catalog=build_delta_catalog(state,batch)
    item=support(state,catalog,target_contribution='implementation_of_retained_rule',
                 predicate_line_handles=[h for h,l in catalog['lines'].items() if l['role']=='added'])
    provider=Provider(reply(state,catalog,{'A0001':[item]}))
    judge=GroundedTraceSemanticJudge('fixture',client=SimpleNamespace(responses=provider))
    result=EventReviewAgent(linker=NoNomination(),judge=judge,profile='event-grounded').run(state,batch)
    assert not result.memory.verified_links and len(result.memory.rejected_interpretations)==1
    assert not result.memory.technical_verification_failures
    assert result.report['investigation_coverage']['artifact_review_records'][0]['candidate_links']==1
