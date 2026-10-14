from copy import deepcopy
from evorationale.agent import EvoRationaleAgent
from evorationale.budget import Budget
from evorationale.model import artifact_key, eligible
from evorationale.retrieval import LocalHybridRetriever, reciprocal_rank_fusion
from evorationale.linking import ExplicitTextLinker


def test_rrf_merges_ranked_lists():
    items=reciprocal_rank_fusion([['a','b'],['b','c']],3)
    assert items[0][0]=='b'
    assert len({x[0] for x in items})==3


def test_retrieval_fails_closed_on_wrong_repo_and_date(approved_state,history):
    from evorationale.model import normalize_artifact
    foreign=deepcopy(history[0]); foreign['repository']='forged/repo';foreign.pop('version_id');foreign.pop('content_sha256')
    after=deepcopy(history[0]);after['timestamp']='2026-02-01T00:00:00Z';after['first_auditable_at']=after['timestamp'];after.pop('version_id');after.pop('content_sha256')
    retriever=LocalHybridRetriever()
    retriever.index(history+[normalize_artifact(foreign),normalize_artifact(after)])
    rows=retriever.search(approved_state,{'query':'benchmark','id':'global'},20)
    assert rows
    assert all(eligible(approved_state,r) for r in rows)
    assert 'pre-001' not in {r['artifact_id'] for r in rows}


def test_retrieval_retains_distinct_versions(approved_state,history):
    from evorationale.model import normalize_artifact
    earlier=next(a for a in history if a['artifact_id']=='inc-017')
    changed={**earlier,'timestamp':'2025-05-01T00:00:00Z',
             'content':'A second stale profile incident contradicted the update assumption.'}
    changed['first_auditable_at']=changed['timestamp'];changed.pop('content_sha256');changed.pop('version_id')
    later=normalize_artifact(changed)
    engine=LocalHybridRetriever();engine.index(history+[later])
    rows=engine.search(approved_state,{'query':'stale profile incident contradicted','id':'global'},20)
    assert len([r for r in rows if r['artifact_id']=='inc-017'])==2


def test_targeted_feedback_reformulates_query(approved_state,history):
    class SequentialRetriever:
        def index(self, artifacts): self.data=artifacts; self.calls=[]
        def search(self,state,question,limit,**kwargs):
            self.calls.append(question.copy())
            selected={'inc-017'} if len(self.calls)==1 else {'pr-088','bench-042'}
            return [a for a in self.data if a['artifact_id'] in selected]
    retriever=SequentialRetriever()
    run=EvoRationaleAgent(retriever=retriever).run(approved_state,history)
    assert len(retriever.calls)==2
    assert retriever.calls[0]['id']=='global'
    assert retriever.calls[1]['id']=='need:E1'
    assert run.report['recommended_outcome']=='REOPEN'
    assert run.report['verification']['status']=='PASS'


def test_agent_does_not_exceed_rounds(approved_state):
    class NoneRetriever:
        def index(self,data): pass
        def search(self,*a,**kw): return []
    agent=EvoRationaleAgent(retriever=NoneRetriever(), budget=Budget(max_rounds=2))
    run=agent.run(approved_state,[])
    assert run.report['budget_usage']['rounds']==2
    assert run.report['verification']['status']=='UNRESOLVED'


def test_agent_does_not_exceed_read_budget(approved_state,history):
    agent=EvoRationaleAgent(budget=Budget(max_artifact_reads=1))
    report=agent.run(approved_state,history).report
    assert report['budget_usage']['unique_artifact_reads']<=1
    assert report['verification']['status']=='UNRESOLVED'


def test_agent_hard_token_budget(approved_state,history):
    report=EvoRationaleAgent(budget=Budget(max_input_tokens=10)).run(approved_state,history).report
    assert report['verification']['status']=='UNRESOLVED'
    assert 'token_limit' in report['stopping_reason']


def test_retrieved_corrupt_candidate_cannot_enter_memory(approved_state,history):
    class BadRetriever:
        def index(self, artifacts): self.data=artifacts
        def search(self,*a,**kw):
            valid=next(x for x in self.data if x['artifact_id']=='inc-017')
            return [{**valid,'content_sha256':'bad-hash'}]
    run=EvoRationaleAgent(retriever=BadRetriever()).run(approved_state,history)
    assert run.report['verified_evidence']==[]
    assert run.report['verification']['status']=='UNRESOLVED'
    assert any('retriever_returned_noncanonical_artifact' in str(x) for x in run.memory.verifier_feedback)
