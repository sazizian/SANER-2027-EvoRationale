"""Behavioral tests for all four permitted recommendations, plus a fake LLM path."""
from copy import deepcopy
import json
from types import SimpleNamespace
import pytest
from evorationale.agent import EvoRationaleAgent
from evorationale.linking import OpenAILinker
from evorationale.planning import OpenAIQueryPlanner
from evorationale.analysis import OpenAIActionPlanner
from evorationale.budget import Budget
from evorationale.verification import EvidenceVerifier, OpenAISemanticJudge
from evorationale.model import normalize_artifact


def evidence(title,content,element,timestamp='2025-06-01T00:00:00Z'):
    return {'artifact_id':title.lower().replace(' ','-'),'source_type':'test',
            'repository':'public-surrogate/profile-service', 'timestamp':timestamp,
            'title':title,'content':content,'tags':[element],
            'source_location':'public-surrogate://test/'+title.lower().replace(' ','-')}


@pytest.mark.parametrize('mode,expected', [
    ('all_support','KEEP'), ('one_weakening','REVISE'), ('contradicting','REOPEN'),
])
def test_four_class_cases(approved_state,mode,expected):
    # Keep just the central elements; explicit issue/release statements produce their links.
    state=deepcopy(approved_state)
    state['goals']=[];state['requirements']=[];state['quality_attributes']=[]
    state['constraints_dependencies']=[];state['implementation_scope']=[]
    if mode=='all_support':
        docs=[evidence('Profile update tests','Profile update tests confirmed the profile updates remain infrequent','profile'),
              evidence('Database benchmark','Database benchmark confirmed database access still exceeds latency target','database')]
    elif mode=='one_weakening':
        docs=[evidence('Profile update tests','Profile update tests weakened the assumptions about infrequent profile updates','profile'),
              evidence('Database benchmark','Database benchmark confirmed database access still exceeds latency target','database')]
    else:
        docs=[evidence('Profile incident','Repeated profile updates contradicted the infrequent profile updates assumption','profile'),
              evidence('Database benchmark','New database benchmark supersedes original database evidence','database')]
    report=EvoRationaleAgent().run(state,docs).report
    assert report['verification']['status']=='PASS'
    assert report['recommended_outcome']==expected


def test_full_model_pipeline_with_fake_responses(approved_state,history):
    budget=Budget(max_input_tokens=64_000)
    class FakeResponses:
        def __init__(self):self.names=[]
        def create(self,**kwargs):
            name=kwargs['text']['format']['name'];self.names.append(name)
            if name=='evidence_question':
                details=json.loads(kwargs['input'])
                obj={'question_id':details['current_need']['id'],
                     'query':'redis profile stale incident database benchmark supersedes'}
            elif name=='proposed_links':
                details=json.loads(kwargs['input'])
                obj={'links':[]}
                for item in details['artifacts']:
                    text=item['content_excerpt']
                    if 'supersedes' in text:
                        obj['links'].append({'artifact_handle':item['artifact_handle'],
                                            'element_id':'E1','relation':'supersedes',
                                            'quote':text,'confidence':0.7})
                    elif 'contradicted' in text:
                        obj['links'].append({'artifact_handle':item['artifact_handle'],
                                            'element_id':'A1','relation':'contradicts',
                                            'quote':text,'confidence':0.7})
            elif name=='semantic_evidence_review':
                obj={'supported':True,'reason':'Exact source explicitly uses relation cue'}
            elif name=='action_proposal':
                obj={'outcome':'REOPEN','p4':[0.03,0.05,0.12,0.8], 'reason':'human should reconsider'}
            else: raise AssertionError(name)
            return SimpleNamespace(output_text=json.dumps(obj))
    responses=FakeResponses()
    client=SimpleNamespace(responses=responses)
    run=EvoRationaleAgent(planner=OpenAIQueryPlanner('test',budget,client),
        linker=OpenAILinker('test',client),
        evidence_verifier=EvidenceVerifier(OpenAISemanticJudge('judge',client)),
        action_planner=OpenAIActionPlanner('test',client,budget=budget),
        budget=budget).run(approved_state,history)
    assert run.report['verification']['status']=='PASS'
    assert run.report['recommended_outcome']=='REOPEN'
    assert {'evidence_question','proposed_links','semantic_evidence_review','action_proposal'} <= set(responses.names)
    assert run.report['human_review_required'] is True
