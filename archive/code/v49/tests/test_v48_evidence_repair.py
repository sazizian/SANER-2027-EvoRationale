"""Generic regressions for a narrow routing repair, not model performance tests."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from evorationale.delta_context import build_delta_catalog
from evorationale.evidence_repair_verification import EvidenceRepairSemanticJudge
from evorationale.evidence_trace_verification import EvidenceTraceSemanticJudge, EVIDENCE_TRACE_INSTRUCTIONS
from test_v46_evidence_trace_verification import case, effect, response, Replies, support_fields

PATCH=("@@ -1,2 +1,4 @@\n-Orders persist through CentralQueue.\n Records record timestamps.\n+\n"
       "+LocalLedger replaces CentralQueue for ordinary order persistence.\n"
       "+CentralQueue remains an optional legacy route.\n")


def evaluate(state,batch,values,cls=EvidenceRepairSemanticJudge):
    catalog=build_delta_catalog(state,batch)
    item=effect(state,catalog,**values)
    fake=Replies(response(state,catalog,{'A0001':[item]}))
    judge=cls('fixture',client=SimpleNamespace(responses=fake))
    accepted,rejected=judge.review_event(state,batch,[])
    return accepted,rejected,judge,fake


def replacement(state,changes=None,cls=EvidenceRepairSemanticJudge):
    state,batch=case(state,PATCH)
    catalog=build_delta_catalog(state,batch)
    values={'change_kind':'mechanism_replacement','effect_basis':'direct_delta',
            'after_line_handles':[h for h,l in catalog['lines'].items() if l['role']=='unchanged'],
            'context_line_handles':[h for h,l in catalog['lines'].items()
                                    if l['role']=='added' and l['text'].strip('+ ')],**(changes or {})}
    return evaluate(state,batch,values,cls)


def test_repair_inherits_v46_prompt_and_exact_schema_without_v47_fields(approved_state):
    state,batch=case(approved_state)
    catalog=build_delta_catalog(state,batch)
    old=EvidenceTraceSemanticJudge('fixture',client=object())
    new=EvidenceRepairSemanticJudge('fixture',client=object())
    assert new.instructions==old.instructions==EVIDENCE_TRACE_INSTRUCTIONS
    assert new._response_schema(catalog,['TRACE_TARGET'])==old._response_schema(catalog,['TRACE_TARGET'])
    assert 'target_contribution' not in str(new._response_schema(catalog,['TRACE_TARGET']))


def test_repair_accepts_added_same_artifact_contract_and_legacy_still_rejects(approved_state):
    accepted,rejected,_,fake=replacement(approved_state)
    assert len(accepted)==1 and not rejected and len(fake.calls)==1
    s=accepted[0]['semantic_assessment']
    assert s['replacement_current_proof_origin']=='SAME_ARTIFACT_ADDED_CONTEXT'
    assert s['semantic_policy']=='evidence-trace-repair' and s['epistemic_status']=='MODEL_ASSESSED'
    assert s['deployed_behavior_verified'] is False
    legacy,feedback,_,_=replacement(approved_state,cls=EvidenceTraceSemanticJudge)
    assert not legacy and feedback[0]['reasons']==['MODEL_ASSESSED:replacement_lacks_both_source_sides']


@pytest.mark.parametrize('change',[
    {'context_line_handles':[]},{'context_establishes_replacement':False},
    {'replacement_is_explicit':False},{'scope_match':False},{'material_target_delta':False},
    {'source_role':'proposal_or_alternative'},{'source_role':'unknown'},
    {'evidence_basis':'unknown'},{'before_line_handles':[]},
])
def test_repair_never_rescues_unestablished_replacement(approved_state,change):
    accepted,rejected,_,_=replacement(approved_state,change)
    assert not accepted and rejected


@pytest.mark.parametrize('role',['removed','unchanged'])
def test_repair_context_must_contain_added_current_contract(approved_state,role):
    state,batch=case(approved_state,PATCH)
    catalog=build_delta_catalog(state,batch)
    values={'change_kind':'mechanism_replacement','effect_basis':'direct_delta',
            'after_line_handles':[h for h,l in catalog['lines'].items() if l['role']=='unchanged'],
            'context_line_handles':[h for h,l in catalog['lines'].items() if l['role']==role]}
    accepted,rejected,_,_=evaluate(state,batch,values)
    assert not accepted and any('replacement_lacks_both_source_sides' in r
                               for f in rejected for r in f['reasons'])


def test_repair_direct_replacement_does_not_borrow_foreign_contract(approved_state):
    state,batch=case(approved_state,'@@ -1,2 +1 @@\n-Orders persist through CentralQueue.\n Records record timestamps.\n',
                    sibling='@@ -20,0 +20 @@\n+LocalLedger replaces CentralQueue for ordinary persistence.\n')
    catalog=build_delta_catalog(state,batch)
    values={'change_kind':'mechanism_replacement','effect_basis':'direct_delta',
            'context_line_handles':[h for h,l in catalog['lines'].items()
                                    if l['artifact_handle']=='A0002' and l['role']=='added']}
    accepted,rejected,_,_=evaluate(state,batch,values)
    assert not accepted and rejected


def test_repair_preserves_v46_adopted_dependency_migration(approved_state):
    state,batch=case(approved_state,sibling='@@ -20,0 +20 @@\n+LocalLedger replaces CentralQueue for ordinary order persistence; CentralQueue remains optional.\n')
    catalog=build_delta_catalog(state,batch)
    values={'context_line_handles':[h for h,l in catalog['lines'].items()
                                    if l['artifact_handle']=='A0002' and l['role']=='added']}
    accepted,rejected,_,_=evaluate(state,batch,values)
    assert len(accepted)==1 and not rejected and accepted[0]['relation']=='supersedes'


@pytest.mark.parametrize('source_type',['git_commit_diff_hunk','document'])
def test_repair_preserves_v46_qualified_current_support(approved_state,source_type):
    content='Approved orders are persisted through CentralQueue by the order writer.'
    if source_type=='git_commit_diff_hunk':content='@@ -1,0 +1 @@\n+'+content+'\n'
    state,batch=case(approved_state,content,source_type=source_type)
    accepted,rejected,_,_=evaluate(state,batch,support_fields())
    assert len(accepted)==1 and not rejected


def test_repair_larger_output_allowance_respects_existing_ceiling(approved_state):
    _,_,_,fake=replacement(approved_state)
    assert fake.calls[0]['max_output_tokens']==6144
    judge=EvidenceRepairSemanticJudge('fixture',client=object())
    assert judge._initial_output_tokens(5)==7200 and judge._initial_output_tokens(100)==16384
