"""v4.1 source-diff capture and narrow code-fact guard regression tests.

All network responses mocked. No GitHub token/OpenAI API used by these tests.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from pathlib import Path
import importlib.util
import json

import pytest

from evorationale.agent import EvoRationaleAgent
from evorationale.budget import Budget
from evorationale.linking import ExplicitTextLinker, candidate_link
from evorationale.model import normalize_artifact, validate_state, element_by_id, normalize_history, artifact_key
from evorationale.patch_facts import check_patch_fact
from evorationale.verification import EvidenceVerifier

ROOT=Path(__file__).resolve().parent.parent
S0=ROOT/'examples/azure/pilot_snapshot/decision_state_ATOMIC_DRAFT.json'
HISTORY=ROOT/'examples/azure/pilot_snapshot/history_LIVE.jsonl'
MANIFEST=ROOT/'examples/azure/pilot_snapshot/github_capture_manifest.json'
spec=importlib.util.spec_from_file_location('enrich_azure_pr_diffs',ROOT/'scripts/enrich_azure_pr_diffs.py')
collector=importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

ARM='''@@ -381,4 +381,8 @@
         },
+        "deployAVNM": {
+            "type": "bool",
+            "defaultValue": false
+        },
@@ -5180,3 +5187,9 @@
+        {
+            // Deploy AVNM
+            "condition": "[and(parameters('deployAVNM'), not(empty(parameters('connectivitySubscriptionId'))))]",
+            "dependsOn": [
+                "[variables('deploymentNames').avnmConnectivityHubDeploymentName]"
+            ],
+        },'''
PORTAL='''@@ -1407,4 +1407,9 @@
+                        {
+                            "name": "deployAVNM",
+                            "type": "Microsoft.Common.CheckBox",
+                            "label": "Deploy Azure Virtual Network Manager - PREVIEW",
+                        },'''


def _state():
    s=json.loads(S0.read_text(encoding='utf-8'))
    s['human_approved']=True
    s['cutoff_at']='2026-10-10T22:00:00Z'  # Test-only: artificial later local audit cutoff
    return validate_state(s)


def _fixture_artifact(content,filename,n=1880):
    return normalize_artifact({
      'artifact_id':f'diff-{n}-{filename}', 'repository':'Azure/Enterprise-Scale',
      'source_type':'pull_request_diff_excerpt',
      'source_location':f'https://github.com/Azure/Enterprise-Scale/pull/{n}/files',
      'title':'GitHub code diff','timestamp':'2026-10-10T18:30:00Z',
      'first_auditable_at':'2026-10-10T18:30:00Z','content':content,
      'metadata':{'file_path':filename,'historical_replay_safe':False,
                  'source_kind':'CURRENT_PR_PATCH_SNAPSHOT'}})


def test_atomic_added_parameter_condition_and_checkbox_excerpts_are_found():
    state=_state()
    outputs=[]
    for fn,patch in [('eslzArm/eslzArm.json',ARM),('eslzArm/eslz-portal.json',PORTAL)]:
        extracted=collector.diff_excerpts(patch,fn,1880)
        assert extracted
        assert all(len(row['content'])<=650 for row in extracted)
        outputs.extend(_fixture_artifact(row['content'],fn) for row in extracted)
    results=[]
    for a in outputs:
        results.extend(ExplicitTextLinker().propose(state,[a],{'id':'global','query':'AVNM'}))
    ids={p['decision_element_id'] for p in results}
    assert {'I1a','I1b','I1c','C1a'}.issubset(ids),ids
    assert 'G1' not in ids  # code changes do not independently prove decision rationale
    verified,feedback=EvidenceVerifier().verify(state,outputs,results)
    assert not feedback,feedback
    assert ids=={p['decision_element_id'] for p in verified}


def test_patch_change_to_file_is_not_proof_of_boolean_parameter_or_condition():
    state=_state();el=element_by_id(state)
    quote='GitHub PR #1880 added ARM/portal code for AVNM in eslzArm/eslzArm.json:\n+  "deployAVNM": "maybe"'
    a=_fixture_artifact(quote,'eslzArm/eslzArm.json')
    ok,reason=check_patch_fact(el['I1a'],a,quote,'supports')
    assert not ok and 'boolean' in reason
    proposed=candidate_link(a,el['I1a'],'supports',quote,0.9)
    good,bad=EvidenceVerifier().verify(state,[a],[proposed])
    assert not good
    assert any('boolean' in x for x in bad[0]['reasons'])


def test_patch_header_cannot_make_unrelated_code_support_atomic_claim():
    state=_state(); el=element_by_id(state)
    quote='GitHub PR #1880 added ARM/portal code for AVNM in eslzArm/eslzArm.json:\n+  "dependsOn": ["otherDeployment"]'
    a=_fixture_artifact(quote,'eslzArm/eslzArm.json')
    for element_id in ('I1a','I1c','C1b'):
        assert not check_patch_fact(el[element_id],a,quote,'supports')[0]
    assert not check_patch_fact(el['G1'],a,quote,'supports')[0]


def test_diff_capture_is_audited_separate_and_requires_human_approval(tmp_path):
    approved=tmp_path/'s0.json'
    approved.write_text(json.dumps(_state()),encoding='utf-8')
    input_sha=collector.file_sha(approved)
    baseline_sha=collector.file_sha(HISTORY)
    now=datetime(2026,10,10,19,0,0,tzinfo=timezone.utc)
    def fake(endpoint,token):
        n=int(endpoint.split('/pulls/')[1].split('/')[0])
        if n!=1880:
            return []
        return [{'filename':'eslzArm/eslzArm.json','status':'modified','patch':ARM},
                {'filename':'eslzArm/eslz-portal.json','status':'modified','patch':PORTAL},
                {'filename':'docs/irrelevant.md','status':'modified','patch':'+ deployAVNM irrelevant'}]
    out=tmp_path/'new'
    info=collector.enrich(decision_path=approved,history_path=HISTORY,
             capture_manifest_path=MANIFEST,output_dir=out,requester=fake,
             clock=lambda:now)
    assert info['old_artifact_versions']==22
    assert info['new_diff_excerpt_versions']>=3
    assert info['historical_replay_certified'] is False
    assert collector.file_sha(approved)==input_sha
    assert collector.file_sha(HISTORY)==baseline_sha
    s=json.loads((out/'decision_state_ENRICHED_DRAFT.json').read_text())
    assert s['human_approved'] is False
    assert s['cutoff_at']>'2026-10-10T19:00:00Z'
    validate_state(s,require_approved=False)
    entries=[json.loads(x) for x in (out/'history_ENRICHED.jsonl').read_text().splitlines()]
    normalized=normalize_history(entries)
    assert len(normalized)==info['total_artifact_versions']
    new=[x for x in normalized if x['source_type']=='pull_request_diff_excerpt']
    assert new and all(x['metadata']['historical_replay_safe'] is False for x in new)
    assert all(x['first_auditable_at']=='2026-10-10T19:00:00Z' for x in new)
    assert len(list((out/'raw_api').glob('*.json')))==4
    with pytest.raises(FileExistsError):
        collector.enrich(decision_path=approved,history_path=HISTORY,
             capture_manifest_path=MANIFEST,output_dir=out,requester=fake,clock=lambda:now)


def test_v41_report_tracks_unattempted_required_needs():
    state=_state()
    rows=normalize_history([json.loads(x) for x in HISTORY.read_text(encoding='utf-8').splitlines() if x.strip()])
    run=EvoRationaleAgent(budget=Budget(max_rounds=2,max_queries=3,
        max_artifact_reads=6,max_input_tokens=50000)).run(state,rows)
    report=run.report['investigation_coverage']
    assert 'required_never_attempted_element_ids' in report
    assert all(row['required'] for row in report['all_need_statuses'] if row['id'].startswith('need:') and row['element_id'] in state['central_element_ids'])
    assert len(report['required_element_ids'])==4
    assert report['required_unresolved_element_ids']


def test_diff_selection_requires_manifest_instead_of_result_cherry_picking(tmp_path):
    s=_state(); approved=tmp_path/'approved.json';approved.write_text(json.dumps(s))
    manifest=json.loads(MANIFEST.read_text());manifest['selected_pr_numbers']=[1880,1880]
    modified=tmp_path/'manifest.json';modified.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='Duplicate PR'):
        collector.enrich(decision_path=approved,history_path=HISTORY,
                         capture_manifest_path=modified,output_dir=tmp_path/'out',
                         requester=lambda *_:[])


def test_added_code_never_auto_approves_architectural_rationale(tmp_path):
    now=datetime(2026,10,10,19,0,0,tzinfo=timezone.utc)
    approved=tmp_path/'approved.json'
    approved.write_text(json.dumps(_state()),encoding='utf-8')
    def fake(endpoint,token):
        n=int(endpoint.split('/pulls/')[1].split('/')[0])
        if n!=1880: return []
        return [{'filename':'eslzArm/eslzArm.json','status':'modified','patch':ARM},
                {'filename':'eslzArm/eslz-portal.json','status':'modified','patch':PORTAL}]
    out=tmp_path/'enriched'
    collector.enrich(decision_path=approved,history_path=HISTORY,
                     capture_manifest_path=MANIFEST,output_dir=out,requester=fake,clock=lambda:now)
    draft=json.loads((out/'decision_state_ENRICHED_DRAFT.json').read_text())
    draft['human_approved']=True  # Test only; not a human-approved research decision.
    state=validate_state(draft)
    history=normalize_history([json.loads(x) for x in (out/'history_ENRICHED.jsonl').read_text().splitlines()])
    run=EvoRationaleAgent(budget=Budget(max_rounds=6,max_queries=12,
                         max_artifact_reads=30,max_input_tokens=120000)).run(state,history)
    ids={a['decision_element_id'] for a in run.report['verified_evidence']}
    assert {'I1a','I1b','I1c'}.issubset(ids)
    assert run.report['composite_coverage'][0]['all_members_supported'] is True
    assert run.report['recommended_outcome']=='REVALIDATE'
    assert run.report['verification']['status']=='UNRESOLVED'
    assert run.report['s0_rationale_sufficiency']['has_documented_central_predecision_rationale'] is False
    assert run.report['stopping_reason']=='initial_rationale_not_documented'


def test_keep_is_possible_when_actual_central_rationale_documented_and_supported():
    state=_state()
    state['assumptions']=[{'id':'A1','text':'AVNM configuration remains optional',
                           'source':'https://github.com/Azure/Enterprise-Scale/pull/1803',
                           'keywords':['AVNM','optional']}]
    state['central_element_ids']=['G1','A1','I1a','I1b','I1c']
    state=validate_state(state)
    # Every central requirement supported by a purpose-built fake judge;
    # this tests action-policy reachability, NOT a scientific gold label.
    from tests.test_atomic_memory_v3 import mk_artifact, StaticRetriever, TargetOnlyLinker, AlwaysPassJudge
    ordered=['G1','A1','I1a','I1b','I1c']
    a=[mk_artifact(state,i,target) for i,target in enumerate(ordered)]
    run=EvoRationaleAgent(retriever=StaticRetriever(),linker=TargetOnlyLinker(),
           evidence_verifier=EvidenceVerifier(AlwaysPassJudge()),
           budget=Budget(max_rounds=5,max_artifact_reads=5,max_input_tokens=100000)).run(state,a)
    assert run.report['s0_rationale_sufficiency']['has_documented_central_predecision_rationale'] is True
    assert run.report['recommended_outcome']=='KEEP'
    assert run.report['verification']['status']=='PASS'
