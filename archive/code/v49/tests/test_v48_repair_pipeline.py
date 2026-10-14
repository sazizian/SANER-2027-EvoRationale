"""Opt-in v4.6-compatible policy, one classification phase and partial needs."""
from types import SimpleNamespace
from evorationale import cli
from evorationale.budget import Budget
from evorationale.delta_context import build_delta_catalog
from evorationale.delta_linking import NoNomination
from evorationale.event_agent import EventReviewAgent
from evorationale.evidence_repair_verification import EvidenceRepairSemanticJudge
from test_v46_evidence_pipeline import Provider,DOCUMENTATION,case,configured_args,reply,support


def test_repair_cli_dispatches_independent_classifier(monkeypatch,tmp_path):
    from evorationale import evidence_repair_verification
    seen=[];monkeypatch.setenv('OPENAI_API_KEY','synthetic-unused-key')
    monkeypatch.setattr(evidence_repair_verification,'EvidenceRepairSemanticJudge',
                        lambda model:seen.append(model) or object())
    agent=cli.build_agent(configured_args(tmp_path,investigation_profile='event-evidence-repair'))
    assert agent.profile=='event-evidence-repair' and isinstance(agent.linker,NoNomination)
    assert seen==['opaque-independent-classifier']


def test_repair_pipeline_keeps_partial_support_and_one_request(approved_state):
    state,batch=case(approved_state,DOCUMENTATION);state['central_element_ids']=['DELTA_TARGET']
    catalog=build_delta_catalog(state,batch);item=support(state,catalog)
    provider=Provider(reply(state,catalog,{'A0001':[item]}))
    judge=EvidenceRepairSemanticJudge('fixture',client=SimpleNamespace(responses=provider))
    result=EventReviewAgent(linker=NoNomination(),judge=judge,profile='event-evidence-repair',
        budget=Budget(max_rounds=1,max_artifact_reads=1,max_input_tokens=100000,max_output_tokens=16384)).run(state,batch)
    assert len(provider.calls)==len(result.memory.verified_links)==1
    assert result.report['nomination_mode']=='none' and result.report['verification']['status']=='UNRESOLVED'
    assert any(n['status']=='PARTIAL_EVIDENCE' for n in result.memory.needs if n['element_id']=='DELTA_TARGET')
