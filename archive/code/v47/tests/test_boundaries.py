from copy import deepcopy
import pytest
from evorationale.model import (ValidationError, validate_state, normalize_artifact,
                               normalize_history, artifact_key, eligible, parse_timestamp)
from evorationale.budget import Budget, BudgetExhausted


def test_valid_decision(state):
    assert validate_state(state)['repository'] == 'public-surrogate/profile-service'

@pytest.mark.parametrize('value', [False, None, 'true', 0])
def test_unapproved_decision_fails(state, value):
    state['human_approved'] = value
    with pytest.raises(ValidationError, match='human_approved'):
        validate_state(state)


def test_missing_repo_fails(state):
    state.pop('repository')
    with pytest.raises(ValidationError, match='repository'):
        validate_state(state)


def test_invalid_timestamp_and_order(state):
    state['cutoff_at'] = '2021-01-01T00:00:00Z'
    with pytest.raises(ValidationError): validate_state(state)
    with pytest.raises(ValidationError): parse_timestamp('2025-09-01T04:00:00')


def test_unresolved_central_id_fails(state):
    state['central_element_ids'] = ['A1','NOT_REAL']
    with pytest.raises(ValidationError): validate_state(state)


def test_duplicate_element_id_fails(state):
    state['goals'][0]['id']='A1'
    with pytest.raises(ValidationError): validate_state(state)


def test_content_hash_rejects_tampering(history):
    a = deepcopy(history[0]); a['content']='replacement text'
    with pytest.raises(ValidationError, match='digest mismatch'): normalize_artifact(a)


def test_exact_versions_not_overwritten(raw_history):
    base = next(a for a in raw_history if a['artifact_id']=='inc-017')
    newer = {**base, 'content':'A revised issue body contradicted the old assumption.',
             'timestamp':'2025-01-01T00:00:00Z','version_id':'edit-2'}
    rows = normalize_history(raw_history+[newer])
    revisions = [a for a in rows if a['artifact_id']=='inc-017']
    assert len(revisions)==2
    assert len({artifact_key(x) for x in revisions})==2


def test_duplicate_version_conflict_fails(raw_history):
    old = {**raw_history[0], 'version_id':'same'}
    changed = {**old, 'content':'modified'}
    with pytest.raises(ValidationError, match='Conflicting'): normalize_history([old,changed])


def test_time_boundary_excludes_before_and_after(approved_state, history):
    a = next(x for x in history if x['artifact_id']=='inc-017')
    assert eligible(approved_state, a)
    assert not eligible(approved_state, {**a,'first_auditable_at':approved_state['accepted_at']})
    assert not eligible(approved_state, {**a,'first_auditable_at':'2026-01-01T00:00:00Z'})
    assert not eligible(approved_state, {**a,'repository':'different/repo'})


def test_cannot_fake_auditable_time_before_event(history):
    a=deepcopy(history[0]);a['first_auditable_at']='2020-01-01T00:00:00Z'
    with pytest.raises(ValidationError): normalize_artifact(a)


def test_budget_counted_per_unique_read():
    class Memory: query_count=0; artifact_reads=[]; token_count=0
    m=Memory();b=Budget(max_queries=1,max_artifact_reads=2,max_input_tokens=200)
    b.charge_query(m)
    with pytest.raises(BudgetExhausted): b.charge_query(m)
    b.charge_reads(m,['a','a'])
    b.charge_reads(m,['a','b'])
    assert len(m.artifact_reads)==2
    with pytest.raises(BudgetExhausted): b.charge_reads(m,['c'])
    with pytest.raises(BudgetExhausted): b.charge_tokens(m,'x'*1000)


def test_negative_budget_fails():
    with pytest.raises(ValueError): Budget(max_rounds=0)
