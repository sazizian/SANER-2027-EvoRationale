from __future__ import annotations
import importlib.util
from pathlib import Path
from datetime import datetime, timezone
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = Path('/mnt/data/EvoRationale_PaperAligned_v2')
# Can also be executed after helper files are copied into the user's EvoRationale project.
if not SRC.exists():
    SRC = ROOT.parent
sys.path.insert(0, str(SRC))
code = ROOT / 'scripts/ingest_azure_avnm_live.py'
spec = importlib.util.spec_from_file_location('live_ingest', code)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture_api(path, token):
    if path.startswith('/search/issues?'):
        return {'total_count':3,'items':[
            {'number':1803,'created_at':'2024-10-17T07:27:36Z','pull_request':{'url':'x'}},
            {'number':1880,'created_at':'2025-01-10T08:35:08Z','pull_request':{'url':'x'}},
            {'number':1896,'created_at':'2025-01-24T08:27:07Z','pull_request':{'url':'x'}},
        ]}
    for n,date in [(1880,'2025-01-10T08:35:08Z'),(1896,'2025-01-24T08:27:07Z')]:
        if path==f'/repos/Azure/Enterprise-Scale/pulls/{n}':
            return {'number':n,'title':f'AVNM change {n}', 'body':'Supports AVNM deployment ' + 'a'*100,
                'created_at':date,'updated_at':'2025-07-01T00:00:00Z','merged_at':'2025-02-01T00:00:00Z',
                'html_url':f'https://github.com/Azure/Enterprise-Scale/pull/{n}'}
        if path.startswith(f'/repos/Azure/Enterprise-Scale/issues/{n}/comments?'):
            return [{'id':n*100,'created_at':'2025-02-01T02:00:00Z','body':'Review shows AVNM support works',
                'html_url':f'https://github.com/Azure/Enterprise-Scale/pull/{n}#issuecomment-1'}]
        if path.startswith(f'/repos/Azure/Enterprise-Scale/pulls/{n}/comments?'):
            return []
        if path.startswith(f'/repos/Azure/Enterprise-Scale/pulls/{n}/commits?'):
            return [{'sha':f'{n:04d}'*10,'commit':{'committer':{'date':'2025-02-01T00:00:00Z'}}}]
    if '/commits/' in path and not '/pulls/' in path:
        sha=path.rsplit('/',1)[-1]
        return {'sha':sha,'commit':{'committer':{'date':'2025-02-01T00:00:00Z'},
            'message':'Update AVNM deployment conditions'},'files':[{'status':'modified','filename':'eslzArm/eslzArm.json'}],
            'html_url':'https://github.com/Azure/Enterprise-Scale/commit/'+sha}
    raise AssertionError('Unexpected URL ' + path)


def state():
    source="https://github.com/Azure/Enterprise-Scale/pull/1803"
    return {
      "episode_id":"unit-pilot-avnm", "decision_id":"GitHub-PR-1803",
      "repository":"Azure/Enterprise-Scale",
      "decision":"Support optional AVNM deployment",
      "accepted_at":"2025-01-10T05:46:36Z",
      "cutoff_at":"2026-10-10T05:36:34Z",
      "human_approved":True,
      "central_element_ids":["G1","I1"],
      "goals":[{"id":"G1","text":"Support optional AVNM deployments", "source":source,
                "keywords":["AVNM","deployment"]}],
      "implementation_scope":[{"id":"I1","text":"AVNM deployment template change", "source":source,
                             "keywords":["AVNM","deployment"]}]
    }


def test_snapshot_is_versioned_not_backdated_and_decision_cutoff_updated(tmp_path):
    result = module.ingest(decision=state(),out=tmp_path, requester=fixture_api,
        now=lambda:datetime(2026,10,10,7,0,tzinfo=timezone.utc),
        max_prs=5,max_content_chars=80)
    assert result['selected_pr_numbers']==[1880,1896]
    records=[json.loads(line) for line in (tmp_path/'history_LIVE.jsonl').read_text().splitlines()]
    assert len(records)==6
    assert all(x['first_auditable_at']=='2026-10-10T07:00:00Z' for x in records)
    assert all(x['timestamp']!='2026-10-10T07:00:00Z' for x in records)
    assert all('PR #1803' not in x['title'] for x in records)
    assert sum(x['source_type']=='commit' for x in records)==2
    assert all(x['metadata']['historical_replay_safe'] is False for x in records)
    assert all(len(x['content'])<=80 for x in records)
    assert all(x['content_sha256'] for x in records)
    s=json.loads((tmp_path/'decision_state_LIVE.json').read_text())
    assert s['human_approved'] is True and s['cutoff_at'] > '2026-10-10T07:00:00Z'
    assert not (tmp_path/'raw'/'secret.json').exists()


def test_rejects_unapproved_s0(tmp_path):
    import pytest
    data=state();data['human_approved']=False
    with pytest.raises(Exception, match='approved'):
        module.ingest(decision=data,out=tmp_path,requester=fixture_api)


def test_rejects_cross_repository(tmp_path):
    import pytest
    data=state();data['repository']='another/repo'
    with pytest.raises(Exception, match='repository'):
        module.ingest(decision=data,out=tmp_path,requester=fixture_api)


def test_rejects_empty_search(tmp_path):
    import pytest
    with pytest.raises(RuntimeError,match='No post-acceptance'):
        module.ingest(decision=state(),out=tmp_path,
            requester=lambda path,token:{'total_count':0,'items':[]},
            now=lambda:datetime(2026,10,10,7,0,tzinfo=timezone.utc))


def test_imported_snapshot_passes_end_to_end_agent_contract(tmp_path):
    from evorationale.agent import EvoRationaleAgent
    from evorationale.budget import Budget
    module.ingest(decision=state(),out=tmp_path,requester=fixture_api,
        now=lambda:datetime(2026,10,10,7,0,tzinfo=timezone.utc))
    imported=json.loads((tmp_path/'decision_state_LIVE.json').read_text())
    history=[json.loads(line) for line in (tmp_path/'history_LIVE.jsonl').read_text().splitlines()]
    result=EvoRationaleAgent(budget=Budget(max_rounds=2,max_queries=4,max_artifact_reads=8)).run(imported,history)
    assert result.status=='AWAITING_HUMAN_REVIEW'
    assert result.report['recommended_outcome'] in {'KEEP','REVALIDATE','REVISE','REOPEN'}
    assert result.report['human_review_required'] is True
    assert result.report['budget_usage']['unique_artifact_reads']<=8
    assert result.report['verification']['status'] in {'PASS','UNRESOLVED'}
