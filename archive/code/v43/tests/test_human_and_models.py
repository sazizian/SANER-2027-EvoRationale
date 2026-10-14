import json
from types import SimpleNamespace
import pytest
from evorationale.agent import EvoRationaleAgent
from evorationale.budget import Budget
from evorationale.analysis import OpenAIActionPlanner, ActionPlanner
from evorationale.planning import OpenAIQueryPlanner
from evorationale.memory import MemoryInProcess, DecisionMemory
from evorationale.human_review import record_human_review
from evorationale.verification import ReportValidator


def test_human_review_required_and_explicit_operator(approved_state,history):
    memory=MemoryInProcess()
    run=EvoRationaleAgent(store=memory).run(approved_state,history)
    assert not memory.get(run.run_id).human_reviews
    result=record_human_review(memory,run.run_id,reviewer_id='qualified_reviewer',
                               action='REQUEST_EVIDENCE',note='Need benchmark provenance')
    assert result['action']=='REQUEST_EVIDENCE'
    assert memory.get(run.run_id).report['human_review_status']=='REQUEST_EVIDENCE'
    assert memory.get(run.run_id).initial_state==approved_state
    with pytest.raises(ValueError):
        record_human_review(memory,run.run_id,reviewer_id='qualified_reviewer',
                            action='ACCEPT',note='second unapproved transition')


def test_cannot_approve_different_decision(approved_state,history):
    m=MemoryInProcess();r=EvoRationaleAgent(store=m).run(approved_state,history)
    changed={**approved_state,'decision_id':'different'}
    with pytest.raises(ValueError,match='same decision'):
        record_human_review(m,r.run_id,reviewer_id='reviewer',action='ACCEPT',note='reason',approved_new_state=changed)


def test_reviewer_identity_and_note_required(approved_state,history):
    m=MemoryInProcess();r=EvoRationaleAgent(store=m).run(approved_state,history)
    with pytest.raises(ValueError):
        record_human_review(m,r.run_id,reviewer_id='',action='ACCEPT',note='yes')


def test_llm_query_planner_cannot_change_question_id(approved_state):
    class Response:
        def create(self,**kwargs):
            return SimpleNamespace(output_text=json.dumps({'question_id':'foreign/question',
                                                           'query':'Invent a new repo scope'}))
    m=DecisionMemory('run',initial_state=approved_state)
    planner=OpenAIQueryPlanner('model',Budget(),client=SimpleNamespace(responses=Response()))
    m.needs=planner.initialize(approved_state)
    result=planner.select(approved_state,m)
    assert result['id']=='global' and result['repository']==approved_state['repository']
    assert result['query_source']=='DETERMINISTIC_FALLBACK'


def test_llm_query_planner_modifies_unresolved_query(approved_state):
    class Response:
        def create(self,**kwargs):
            return SimpleNamespace(output_text=json.dumps({'question_id':'global',
                            'query':'redis stale update incident benchmark invalidation'}))
    m=DecisionMemory('run',initial_state=approved_state)
    planner=OpenAIQueryPlanner('model',Budget(),client=SimpleNamespace(responses=Response()))
    m.needs=planner.initialize(approved_state)
    result=planner.select(approved_state,m)
    assert result['query_source']=='LLM_REFORMULATION'
    assert result['query']=='redis stale update incident benchmark invalidation'


def test_llm_action_planner_p4_and_independent_gating(approved_state,history):
    from evorationale.model import normalize_history
    from evorationale.linking import ExplicitTextLinker
    from evorationale.verification import EvidenceVerifier
    a=next(x for x in history if x['artifact_id']=='inc-017')
    question={'id':'global'}
    links=ExplicitTextLinker().propose(approved_state,[a],question)
    accepted,_=EvidenceVerifier().verify(approved_state,history,links)
    class Responses:
        def create(self,**kwargs):
            return SimpleNamespace(output_text=json.dumps({'outcome':'REOPEN',
                'p4':[0.05,0.05,0.1,0.8],'reason':'Reconsider original rationale'}))
    planner=OpenAIActionPlanner('mock-model',client=SimpleNamespace(responses=Responses()))
    r=planner.compose(approved_state,accepted,[])
    assert r['confidence_kind']=='MODEL_PROPOSED_NOT_CALIBRATED'
    assert sum(r['outcome_probabilities'].values())==pytest.approx(1.0)
    assert ReportValidator().validate(approved_state,accepted,r)['status']=='PASS'


def test_validator_blocks_keep_despite_verified_contradiction(approved_state,history):
    from evorationale.model import elements
    from evorationale.linking import candidate_link
    from evorationale.verification import EvidenceVerifier
    a=next(x for x in history if x['artifact_id']=='inc-017')
    el=next(x for x in elements(approved_state) if x['id']=='A1')
    x=candidate_link(a,el,'contradicts',a['content'],0.8)
    accepted,_=EvidenceVerifier().verify(approved_state,history,[x])
    report=ActionPlanner().compose(approved_state,accepted,[])
    report['recommended_outcome']='KEEP'
    report['outcome_probabilities']={'KEEP':0.8,'REVALIDATE':0.1,'REVISE':0.05,'REOPEN':0.05}
    assert 'keep_not_supported_by_adverse_evidence' in ReportValidator().validate(approved_state,accepted,report)['failures']


def test_validator_blocks_reopen_with_no_direct_central_drift(approved_state,history):
    report=ActionPlanner().compose(approved_state,[],[])
    report['recommended_outcome']='REOPEN'
    report['outcome_probabilities']={'KEEP':0.05,'REVALIDATE':0.05,'REVISE':0.1,'REOPEN':0.8}
    assert 'reopen_not_supported_by_central_rationale' in ReportValidator().validate(approved_state,[],report)['failures']
