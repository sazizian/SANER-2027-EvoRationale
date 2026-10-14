import pytest
from evorationale.evaluation import (set_precision_recall_f1,multiclass_macro_f1,
    multilabel_macro_f1,paired_repository_bootstrap,holm_adjust,paired_wilcoxon,
    repository_weighted_scores, OUTCOME_LABELS, reference_sets)
from evorationale.experiments import ExperimentalRegistry, UnavailableStudyImplementation
from evorationale.budget import Budget


def test_f1_zero_and_nonzero():
    assert set_precision_recall_f1(set(),{'a'})['f1']==0
    assert set_precision_recall_f1({'a','b'},{'b'})['f1']==pytest.approx(2/3)


def test_macro_f1_four_outcomes():
    predictions=['KEEP','REOPEN','REVISE','REVALIDATE']
    assert multiclass_macro_f1(predictions,predictions,OUTCOME_LABELS)==1.0
    assert multiclass_macro_f1(['KEEP']*4,predictions,OUTCOME_LABELS)<0.3


def test_multilabel_f1():
    assert multilabel_macro_f1([{'assumption_drift'}],[{'assumption_drift'}])>0


def test_repository_weighted_aggregation():
    rows=[]
    for repo in ['R1','R2']:
        for rep in range(2):
            for outcome in OUTCOME_LABELS:
                rows.append({'repository':repo,'repetition':rep,'predicted_outcome':outcome,'gold_outcome':outcome,
                    'predicted_drift':['assumption_drift'],'gold_drift':['assumption_drift'],
                    'evidence_f1':0.75,'link_f1':0.5,'relation_f1':0.5,'ucr':0.0})
    summary=repository_weighted_scores(rows)
    assert summary['outcome_macro_f1']==1.0
    assert summary['evidence_f1']==0.75
    assert summary['ucr']==0.0


def test_bootstrap_is_deterministic():
    left={'r1':0.9,'r2':0.8,'r3':0.7}
    right={'r1':0.6,'r2':0.5,'r3':0.5}
    first=paired_repository_bootstrap(left,right,iterations=500,seed=2027)
    second=paired_repository_bootstrap(left,right,iterations=500,seed=2027)
    assert first==second
    assert first['paired_difference']>0


def test_holm_monotonic():
    p=holm_adjust([.01,.03,.02,.9])
    assert p[0]==pytest.approx(.04)
    assert p[3]==pytest.approx(.9)


def test_wilcoxon_requires_repo_match_and_is_computed():
    values={f'r{i}':0.90+i/1000 for i in range(15)}
    comparator={f'r{i}':0.7+i/1000 for i in range(15)}
    r=paired_wilcoxon(values,comparator)
    assert r['pvalue']<0.05
    assert r['r_rank_biserial']>0
    with pytest.raises(ValueError): paired_repository_bootstrap({'r1':1}, {'r2':1})


def test_unavailable_external_baselines_refuse_fabricated_results(approved_state,history):
    registry=ExperimentalRegistry()
    with pytest.raises(UnavailableStudyImplementation,match='no validated'):
        registry.run('linkanchor_adapted',state=approved_state,history=history,budget=Budget())
    with pytest.raises(ValueError):
        registry.register('invented_own_method',lambda **x:None)


def test_reference_sets_accepts_exact_version_only_records():
    from evorationale.evaluation import reference_sets
    # In the research format a link is uniquely identified by its exact version key;
    # it need not redundantly include an artifact_id.
    link = {'artifact_key': 'r::A-1::v2', 'decision_element_id': 'assumption-1',
            'relation': 'contradicts'}
    assert reference_sets({'verified_evidence': [link]}, {'evidence_links': [link]})['links']['f1'] == 1.0


def test_pratt_zero_rank_handling():
    pytest = __import__('pytest')
    scipy = pytest.importorskip('scipy.stats')
    from evorationale.evaluation import paired_wilcoxon
    left = {'a': 1, 'b': 3, 'c': 2, 'd': 4}
    right = {'a': 1, 'b': 1, 'c': 3, 'd': 1}
    result = paired_wilcoxon(left, right)
    differences = [0,2,-1,3]
    ranks = scipy.rankdata([abs(x) for x in differences])
    wanted = (ranks[1]+ranks[3]-ranks[2])/(ranks[1]+ranks[3]+ranks[2])
    assert result['r_rank_biserial'] == pytest.approx(wanted)
