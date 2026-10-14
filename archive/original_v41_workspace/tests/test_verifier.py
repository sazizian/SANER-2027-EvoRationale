from copy import deepcopy
import pytest
from evorationale.linking import candidate_link, ExplicitTextLinker
from evorationale.verification import EvidenceVerifier, ReportValidator, exact_claim_for_link
from evorationale.model import elements, artifact_key
from evorationale.agent import EvoRationaleAgent


def _valid_link(s, h):
    a=next(x for x in h if x['artifact_id']=='inc-017')
    element=next(x for x in elements(s) if x['id']=='A1')
    return candidate_link(a,element,'contradicts',a['content'],0.75,'need:A1')


def test_valid_explicit_quote_passes(approved_state, history):
    verified,feedback=EvidenceVerifier().verify(approved_state,history,[_valid_link(approved_state,history)])
    assert len(verified)==1 and feedback==[]
    assert verified[0]['semantic_check'].startswith('EXTRACTIVE')

@pytest.mark.parametrize('field,value,expected', [
    ('artifact_key','other::artifact::bad','unknown_artifact_version'),
    ('repository','foreign/repo','provenance_mismatch:repository'),
    ('artifact_id','invented','provenance_mismatch:artifact_id'),
    ('version_id','fake-revision','provenance_mismatch:version_id'),
    ('source_location','https://evil.invalid/forged','provenance_mismatch:source_location'),
    ('timestamp','2020-01-01T00:00:00Z','provenance_mismatch:timestamp'),
    ('first_auditable_at','2019-01-01T00:00:00Z','provenance_mismatch:first_auditable_at'),
    ('content_sha256','00'*32,'provenance_mismatch:content_sha256'),
    ('decision_element_id','nonexistent','unknown_or_mismatched_decision_element'),
    ('relation','supports','relation_is_not_explicitly_supported_by_quote'),
    ('quote','The source proves all decisions are valid','quote_not_in_exact_artifact_version'),
    ('relation_confidence',1.7,'invalid_confidence'),
])
def test_attack_is_rejected(approved_state,history,field,value,expected):
    record=_valid_link(approved_state,history);record[field]=value
    verified,feedback=EvidenceVerifier().verify(approved_state,history,[record])
    assert not verified
    assert expected in feedback[0]['reasons']


def test_wrong_element_type_is_rejected(approved_state,history):
    link=_valid_link(approved_state,history);link['decision_element_type']='goals'
    good,errors=EvidenceVerifier().verify(approved_state,history,[link])
    assert not good and 'unknown_or_mismatched_decision_element' in errors[0]['reasons']


def test_model_can_not_validate_negated_relation(approved_state,history):
    a=next(x for x in history if x['artifact_id']=='inc-017')
    modified={**a,'content':'The new incident did not contradict the update assumption.'}
    from evorationale.model import normalize_artifact
    modified.pop('content_sha256'); modified.pop('version_id')
    modified=normalize_artifact(modified)
    e=next(x for x in elements(approved_state) if x['id']=='A1')
    link=candidate_link(modified,e,'contradicts',modified['content'],0.7)
    yes,no=EvidenceVerifier().verify(approved_state,[modified],[link])
    assert not yes


def test_evidence_for_other_repository_is_rejected(approved_state, history):
    record=deepcopy(next(x for x in history if x['artifact_id']=='inc-017'))
    record['repository']='other/team'
    from evorationale.model import normalize_artifact
    record=normalize_artifact(record)
    elem=next(x for x in elements(approved_state) if x['id']=='A1')
    link=candidate_link(record,elem,'contradicts',record['content'],0.7)
    yes,no=EvidenceVerifier().verify(approved_state,history+[record],[link])
    assert not yes and 'unauthorized_repository_or_time' in no[0]['reasons']


def test_report_validator_rejects_fake_material_claim(approved_state,history):
    accepted,_=EvidenceVerifier().verify(approved_state,history,[_valid_link(approved_state,history)])
    from evorationale.analysis import ActionPlanner
    report=ActionPlanner().compose(approved_state,accepted,[])
    assert ReportValidator().validate(approved_state,accepted,report)['status']=='PASS'
    report['material_claims'][0]['text']='The repository proves this company is safe forever.'
    assert ReportValidator().validate(approved_state,accepted,report)['status']=='FAIL'


def test_report_validator_rejects_zero_claim_and_drift_injection(approved_state,history):
    accepted,_=EvidenceVerifier().verify(approved_state,history,[_valid_link(approved_state,history)])
    from evorationale.analysis import ActionPlanner
    report=ActionPlanner().compose(approved_state,accepted,[])
    report['material_claims']=[]
    assert 'zero_material_claims' in ReportValidator().validate(approved_state,accepted,report)['failures']
    report['material_claims']=[exact_claim_for_link(x) for x in accepted]
    report['drift_types']=['quality_attribute_drift']
    assert 'unsupported_drift_types' in ReportValidator().validate(approved_state,accepted,report)['failures']


def test_report_validator_rejects_forged_evidence(approved_state,history):
    accepted,_=EvidenceVerifier().verify(approved_state,history,[_valid_link(approved_state,history)])
    from evorationale.analysis import ActionPlanner
    report=ActionPlanner().compose(approved_state,accepted,[])
    report['verified_evidence'][0]['quote']='Never in original'
    assert ReportValidator().validate(approved_state,accepted,report)['status']=='FAIL'


def test_agent_creates_human_review_with_verification(approved_state,history):
    agent=EvoRationaleAgent()
    out=agent.run(approved_state,history)
    assert out.status=='AWAITING_HUMAN_REVIEW'
    assert out.report['recommended_outcome']=='REOPEN'
    assert out.report['verification']['status']=='PASS'
    assert out.report['human_review_status']=='PENDING'
    assert out.report['unsupported_claim_rate']==0.0
    assert out.report['budget_usage']['rounds']<=3
    assert all(x['quote'] for x in out.report['verified_evidence'])


def test_no_evidence_returns_unresolved_not_pass(approved_state):
    result=EvoRationaleAgent().run(approved_state,[])
    assert result.report['recommended_outcome']=='REVALIDATE'
    assert result.report['verification']['status']=='UNRESOLVED'
    assert result.report['unsupported_claim_rate']==1.0
    assert result.report['zero_claim_report'] is True


def test_copy_of_result_in_memory_is_independent(approved_state,history):
    from evorationale.memory import MemoryInProcess
    mem=MemoryInProcess();run=EvoRationaleAgent(store=mem).run(approved_state,history)
    assert mem.checkpoint_counts[run.run_id]>=2
    separate=mem.get(run.run_id)
    separate.status='CORRUPTED_LOCAL_COPY'
    assert mem.get(run.run_id).status=='AWAITING_HUMAN_REVIEW'
