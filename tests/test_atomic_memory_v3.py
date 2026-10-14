"""Regression tests for AVNM pilot: atomic S0, bounded new reads, caching, coverage."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from evorationale.agent import EvoRationaleAgent
from evorationale.analysis import composite_coverage
from evorationale.atomic_state import propose_azure_avnm_atomic_state
from evorationale.budget import Budget
from evorationale.linking import candidate_link
from evorationale.model import ValidationError, artifact_key, element_by_id, normalize_artifact, validate_state
from evorationale.state_builder import approve_draft
from evorationale.verification import EvidenceVerifier

ANCHOR = Path(__file__).resolve().parent.parent / 'examples' / 'azure' / 'original_state_DRAFT.json'


def original_approved():
    src = json.loads(ANCHOR.read_text(encoding='utf-8'))
    return approve_draft(src, ['G1', 'I1'])


def atomic_approved():
    original = original_approved()
    return approve_draft(propose_azure_avnm_atomic_state(original), ['G1', 'I1a', 'I1b', 'I1c'])


def mk_artifact(state, index, target_id, *, large=False):
    quote = f'Independent tests support the documented behavior for {target_id}: AVNM deployment.'
    if large:
        quote = 'large irrelevant metadata ' * 1000 + quote
    stamp = (datetime.fromisoformat(state['accepted_at'].replace('Z', '+00:00')) +
             timedelta(days=20 + index)).isoformat().replace('+00:00','Z')
    return normalize_artifact({
        'repository': state['repository'], 'artifact_id': f'test-{index}',
        'title': f'Architecture change {target_id}', 'source_type': 'test',
        'source_location': f'https://github.com/Azure/Enterprise-Scale/pull/{2000+index}',
        'timestamp': stamp, 'first_auditable_at': stamp, 'content': quote,
        'tags': [target_id], 'metadata': {'target_id': target_id},
    })


class StaticRetriever:
    def __init__(self): self.calls = []
    def index(self, artifacts): self.artifacts = list(artifacts)
    def search(self, state, question, limit, **kwargs):
        self.calls.append(question['id'])
        return self.artifacts[:limit]


class TargetOnlyLinker:
    def propose(self, state, artifacts, question):
        result = []
        for a in artifacts:
            target = a['metadata']['target_id']
            if question['id'] == 'global' and target != 'G1':
                continue
            if question['id'] != 'global' and target != question['element_id']:
                continue
            result.append(candidate_link(a, element_by_id(state)[target], 'supports', a['content'],
                                         .83, question['id']))
        return result


class AlwaysPassJudge:
    def supports(self, element, quote, relation): return (True, 'DETERMINISTIC_FAKE_JUDGE_FOR_TESTS')


def test_atomic_draft_refuses_autoapproval_and_preserves_source():
    source = original_approved()
    before = deepcopy(source)
    draft = propose_azure_avnm_atomic_state(source)
    assert before == source
    assert draft['human_approved'] is False
    assert draft['episode_id'] != source['episode_id']
    assert draft['accepted_at'] == source['accepted_at']
    assert draft['cutoff_at'] == source['cutoff_at']
    assert draft['original_episode_id'] == source['episode_id']
    assert all(x['source'] == source['implementation_scope'][0]['source']
               for x in draft['implementation_scope'])
    assert {x['id'] for x in draft['implementation_scope']} == {'I1a','I1b','I1c'}
    assert {x['id'] for x in draft['constraints_dependencies']} == {'C1a','C1b'}
    with pytest.raises(ValidationError, match='human_approved'):
        validate_state(draft)
    approved = approve_draft(draft, ['G1', 'I1a', 'I1b', 'I1c'])
    assert validate_state(approved) == approved


def test_atomic_drafter_refuses_changed_case():
    original = original_approved()
    original['implementation_scope'][0]['text'] = 'Different architecture decision'
    with pytest.raises(ValueError, match='Original I1'):
        propose_azure_avnm_atomic_state(original)
    original = original_approved()
    original['repository'] = 'unrelated/other'
    with pytest.raises(ValueError, match='scoped'):
        propose_azure_avnm_atomic_state(original)


def test_composite_coverage_requires_all_members():
    state = atomic_approved()
    a = {'decision_element_id':'I1a','relation':'supports'}
    b = {'decision_element_id':'I1b','relation':'supports'}
    c = {'decision_element_id':'I1c','relation':'supports'}
    coverage = composite_coverage(state, [a,b])
    assert not coverage[0]['all_members_supported']
    assert coverage[0]['missing_member_ids'] == ['I1c']
    assert composite_coverage(state, [a,b,c])[0]['all_members_supported'] is True
    assert composite_coverage(state, [a,b,c,{**a,'relation':'weakens'}])[0]['all_members_supported'] is False
    with pytest.raises(ValidationError, match='composite'):
        corrupt=deepcopy(state); corrupt['composite_groups'][0]['member_ids']=['I1a','I1a']
        validate_state(corrupt)


def test_budget_preserved_across_four_rounds_and_all_atomic_coverage():
    state = atomic_approved()
    sequence = ['G1','I1a','I1b','I1c']
    artifacts = [mk_artifact(state,i,el) for i,el in enumerate(sequence)]
    retriever = StaticRetriever()
    agent = EvoRationaleAgent(retriever=retriever, linker=TargetOnlyLinker(),
        evidence_verifier=EvidenceVerifier(AlwaysPassJudge()),
        budget=Budget(max_rounds=4,max_artifact_reads=4,max_input_tokens=100_000))
    run = agent.run(state, artifacts)
    assert retriever.calls == ['global','need:I1a','need:I1b','need:I1c']
    # v4.1 intentionally does not emit KEEP when the central S0 only
    # documents implementation/goal and has no initial rationale anchor.
    assert run.report['recommended_outcome'] == 'REVALIDATE'
    assert run.report['verification']['status'] == 'UNRESOLVED'
    assert run.report['s0_rationale_sufficiency']['has_documented_central_predecision_rationale'] is False
    assert run.report['composite_coverage'][0]['all_members_supported'] is True
    assert len(run.memory.artifact_reads) == 4
    assert [len(row['new_artifact_keys']) for row in run.trace] == [1,1,1,1]
    assert run.report['budget_usage']['rounds'] == 4


def test_verifier_cache_skips_identical_rejection_across_different_questions():
    state = atomic_approved()
    artifact = mk_artifact(state,0,'I1a')
    class SameLinker:
        def propose(self,state,artifacts,question):
            if not artifacts: return []
            return [candidate_link(artifacts[0],element_by_id(state)['I1a'],'supports',
                                   artifacts[0]['content'],.8,question['id'])]
    class RejectingVerifier:
        def __init__(self): self.calls=0
        def verify(self,state,history,proposed):
            self.calls += 1
            return [], [{'element_id':'I1a','reasons':['test_semantic_rejection']}]
    verifier=RejectingVerifier()
    run=EvoRationaleAgent(retriever=StaticRetriever(),linker=SameLinker(),
          evidence_verifier=verifier,budget=Budget(max_rounds=3,max_artifact_reads=3)).run(state,[artifact])
    assert verifier.calls == 1
    assert len(run.memory.reviewed_proposals) == 1
    assert run.report['verification']['status']=='UNRESOLVED'
    assert len([f for f in run.memory.verifier_feedback if 'test_semantic_rejection' in str(f)]) == 1
    assert any(row.get('cached_verifier_decisions')==1 for row in run.trace[1:])


def test_changed_quote_requires_new_verification():
    state = atomic_approved()
    artifact = mk_artifact(state,0,'I1a')
    class ChangingLinker:
        def propose(self,state,artifacts,question):
            if not artifacts: return []
            quote = 'Independent tests support' if question['id']=='global' else 'documented behavior'
            return [candidate_link(artifacts[0],element_by_id(state)['I1a'],'supports',
                                   quote,.8,question['id'])]
    class RejectingVerifier:
        def __init__(self):self.calls=0
        def verify(self,*args):
            self.calls+=1
            return [],[{'element_id':'I1a','reasons':['fake']}]
    verifier=RejectingVerifier()
    run=EvoRationaleAgent(retriever=StaticRetriever(),linker=ChangingLinker(),
          evidence_verifier=verifier,budget=Budget(max_rounds=3,max_artifact_reads=3)).run(state,[artifact])
    assert verifier.calls == 2
    assert len(run.memory.reviewed_proposals) == 2


def test_oversized_document_does_not_exhaust_all_remaining_token_budget():
    state = atomic_approved()
    enormous = mk_artifact(state,0,'G1',large=True)
    small = mk_artifact(state,1,'G1')
    run=EvoRationaleAgent(retriever=StaticRetriever(),
          budget=Budget(max_rounds=1,max_artifact_reads=2,max_input_tokens=2800)).run(state,[enormous,small])
    assert any(artifact_key(enormous) in row['skipped_due_to_token_budget'] for row in run.trace)
    assert artifact_key(small) in run.memory.artifact_reads
    assert artifact_key(enormous) not in run.memory.artifact_reads
    assert run.report['budget_usage']['estimated_input_tokens'] <= 2800


def test_transient_semantic_judge_error_is_not_cached_and_can_recover():
    state = atomic_approved()
    artifact = mk_artifact(state,0,'I1a')
    class SameLinker:
        def propose(self,state,artifacts,question):
            if not artifacts: return []
            return [candidate_link(artifacts[0],element_by_id(state)['I1a'],'supports',
                                   artifacts[0]['content'],.8,question['id'])]
    class FlakyVerifier:
        def __init__(self): self.calls=0
        def verify(self,state,history,proposals):
            self.calls += 1
            if self.calls==1:
                return [],[{'element_id':'I1a','reasons':['semantic_judge_error:response_incomplete']}]
            return [{**proposals[0],'verifier_status':'PASS','semantic_check':'TEST_ONLY'}],[]
    verifier=FlakyVerifier()
    run=EvoRationaleAgent(retriever=StaticRetriever(),linker=SameLinker(),
         evidence_verifier=verifier,
         budget=Budget(max_rounds=3,max_artifact_reads=3)).run(state,[artifact])
    assert verifier.calls==2
    assert len(run.memory.technical_verification_failures)==1
    assert not any('semantic_judge_error:' in str(x) for x in run.memory.rejected_interpretations)
    assert len(run.memory.reviewed_proposals)==1
    assert len(run.memory.verified_links)==1


def test_invalid_score_is_not_approved_through_cached_verdict():
    state = atomic_approved()
    artifact = mk_artifact(state,0,'I1a')
    class BadScoreOnRetry:
        def __init__(self): self.calls=0
        def propose(self,state,artifacts,question):
            if not artifacts:return []
            self.calls+=1
            return [candidate_link(artifacts[0],element_by_id(state)['I1a'],'supports',
                  artifacts[0]['content'],.85 if self.calls==1 else 3.0,question['id'])]
    class Counter:
        def __init__(self):self.calls=0
        def verify(self,state,history,proposals):
            self.calls+=1
            return [],[{'element_id':'I1a','reasons':['not_enough_content']}]
    judge=Counter()
    run=EvoRationaleAgent(retriever=StaticRetriever(),linker=BadScoreOnRetry(),
       evidence_verifier=judge,budget=Budget(max_rounds=2,max_artifact_reads=2)).run(state,[artifact])
    # The verdict cache must NOT short-circuit verification for invalid confidence.
    assert judge.calls==2
    assert len(run.memory.reviewed_proposals)==1


def test_retrieval_candidate_limit_allows_later_unseen_artifacts():
    state = atomic_approved()
    artifacts = [mk_artifact(state,i,'I1a') for i in range(20)]
    retriever=StaticRetriever()
    # No eligible links: all three investigation rounds remain necessary.
    run=EvoRationaleAgent(retriever=retriever,
        budget=Budget(max_rounds=3,max_artifact_reads=9,max_input_tokens=300_000)).run(state,artifacts)
    assert run.report['budget_usage']['rounds']==3
    assert len(run.memory.artifact_reads)==9
    assert artifact_key(artifacts[8]) in run.memory.artifact_reads
    assert [len(t['new_artifact_keys']) for t in run.trace]==[3,3,3]
    assert len(retriever.calls)==3


def test_draft_script_direct_execution_imports_this_checkout(tmp_path):
    import subprocess
    import sys
    state_file = tmp_path/'source.json'
    state_file.write_text(json.dumps(original_approved()),encoding='utf-8')
    generated = tmp_path/'atomic.json'
    command = [sys.executable, str(Path(__file__).resolve().parent.parent/'scripts/propose_atomic_azure_state.py'),
               '--source',str(state_file),'--output',str(generated)]
    proc = subprocess.run(command,cwd=tmp_path,text=True,capture_output=True)
    assert proc.returncode == 0, proc.stderr
    new = json.loads(generated.read_text(encoding='utf-8'))
    assert new['human_approved'] is False
    second = subprocess.run(command,cwd=tmp_path,text=True,capture_output=True)
    assert second.returncode != 0
    assert 'Refusing to overwrite' in second.stderr
