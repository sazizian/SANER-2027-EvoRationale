"""Malformed model and identifier inputs fail closed instead of bypassing gates."""
from copy import deepcopy
import pytest
from evorationale.model import ValidationError, normalize_artifact, validate_state
from evorationale.verification import EvidenceVerifier, ReportValidator
from evorationale.analysis import ActionPlanner


def test_version_key_delimiter_collision_rejected(approved_state, history):
    state=deepcopy(approved_state)
    state['repository']='a::b'
    with pytest.raises(ValidationError, match='separator'):
        validate_state(state)
    for name in ('repository','artifact_id','version_id'):
        doc=deepcopy(history[0]); doc[name]='prefix::suffix'
        with pytest.raises(ValidationError, match='separator'):
            normalize_artifact(doc)


def test_malformed_proposed_links_are_rejected(approved_state, history):
    verifier=EvidenceVerifier()
    assert verifier.verify(approved_state,history, 'not a list')[0]==[]
    got,feedback=verifier.verify(approved_state,history,[42,None,False])
    assert not got and len(feedback)==3
    assert all(item['reasons']==['malformed_evidence_link'] for item in feedback)


def test_malformed_report_evidence_fails(approved_state):
    report=ActionPlanner().compose(approved_state,[],[])
    report['verified_evidence']=['not a link']
    result=ReportValidator().validate(approved_state,[],report)
    assert result['status']=='FAIL'
    assert 'reported_evidence_not_equal_to_verified_memory' in result['failures']
