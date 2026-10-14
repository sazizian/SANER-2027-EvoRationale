"""Synthetic provenance workflows for pair release; never hosted accuracy."""
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from test_v48_development_tools import (inputs48, command as command48, complete as complete48, inputs47,
    ROOT,DECISION,HISTORY,sha,write,inputs46,prepared_v45_inputs,prepared_inputs)

PARENT48_HASH='ab82ceb7019d8534515dd5e6ead0153b3d92bed545c6e251bc64e97d2a816853'


def command(script,args):
    if script=='prepare_v49.py':
        wrapper=(f'import sys; sys.path.insert(0,{str(ROOT/"development_tools")!r}); '
                 'import prepare_v49; from _score_core import code_tree_hash; '
                 f'prepare_v49.EXPECTED_V49_CODE_SHA256=code_tree_hash({str(ROOT)!r}); prepare_v49.main()')
        invocation=[sys.executable,'-c',wrapper,*map(str,args)]
    else:invocation=[sys.executable,str(ROOT/'development_tools'/script),*map(str,args)]
    return subprocess.run(invocation,cwd=ROOT,capture_output=True,text=True)


@pytest.fixture
def inputs49(inputs48):
    api,offline,frozen,p43,p44,p45,p46,p47,p48,args48,_=inputs48
    result=command48('prepare_v48.py',args48);assert result.returncode==0,result.stderr
    cfg=json.loads((p48/'DEV_PREP_MANIFEST.json').read_text())
    cfg['v48_python_sha256']=PARENT48_HASH;write(p48/'DEV_PREP_MANIFEST.json',cfg)
    complete48(p48)
    metrics=json.loads((p47/'score/metrics.json').read_text())
    metrics.update(status='V48_DEVELOPMENT_ONLY_POST_RUN_REFERENCE_COMPARISON',
                   v48_code_sha256=PARENT48_HASH,v48_run_report_sha256=sha(p48/'run/report.json'),
                   nomination_mode='none')
    write(p48/'score/metrics.json',metrics)
    (p48/'score/link_errors.csv').write_text('scope,verdict,hunk_id,atomic_s0_id,relation,reference_hunk_relation,temporal_basis\n')
    write(p48/'score/SCORE_RECEIPT.json',{'status':'V48_SCORE_COMMITTED',
        'run_report_sha256':sha(p48/'run/report.json'),'core_sha256':PARENT48_HASH,
        'frozen_manifest_sha256':cfg['frozen_manifest_sha256'],
        'metrics_sha256':sha(p48/'score/metrics.json'),'link_errors_sha256':sha(p48/'score/link_errors.csv')})
    ev=p48.parent/'evaluation49';args=list(args48)
    args[args.index('--output')+1]=ev;args.extend(['--previous-v48',p48])
    before={p:sha(p) for folder in (api,offline,frozen,p43,p44,p45,p46,p47,p48)
            for p in folder.rglob('*') if p.is_file()}
    return api,offline,frozen,p43,p44,p45,p46,p47,p48,ev,args,before


def complete(evaluation,evidence=None):
    from evorationale.model import validate_state
    cfg=json.loads((evaluation/'DEV_PREP_MANIFEST.json').read_text())
    report={'verified_evidence':evidence or [],'verification':{'status':'UNRESOLVED'}}
    write(evaluation/'run/report.json',report)
    run_id='SIMULATED_V49_NO_PROVIDER';relative=f'checkpoints/{run_id}.json'
    write(evaluation/'run/manifest.json',{'run_id':run_id,'mode':'api','investigation_profile':'event-pair-reviewed',
        'nomination_mode':'none','max_provider_requests':cfg['budgets']['max_provider_requests'],'decision_sha256':cfg['runtime_s0_sha256'],'history_sha256':cfg['history_sha256'],
        'report_sha256':sha(evaluation/'run/report.json')})
    write(evaluation/relative,{'run_id':run_id,'report':report,
        'initial_state':validate_state(json.loads((evaluation/'inputs'/DECISION).read_text()))})
    write(evaluation/'RUN_RECEIPT.json',{'run_id':run_id,'mode':'api','investigation_profile':'event-pair-reviewed',
        'nomination_mode':'none','status':'V49_DEV_HOSTED_RUN_COMPLETED_AND_HASHED',
        'code_tree_sha256':cfg['v49_python_sha256'],'model':cfg['models'],'nominal_budgets':cfg['budgets'],
        **{key:cfg[key] for key in ('parent_v44_models','parent_v45_models','parent_v46_models','parent_v47_models','parent_v48_models','policy_change_note','semantic_phase_config')},
        'prep_sha256':sha(evaluation/'DEV_PREP_MANIFEST.json'),
        'run_manifest_sha256':sha(evaluation/'run/manifest.json'),'run_report_sha256':sha(evaluation/'run/report.json'),
        'checkpoint_relative_path':relative,'checkpoint_sha256':sha(evaluation/relative)})


def scoring_args(inputs):
    api,offline,frozen,p43,p44,p45,p46,p47,p48,ev,*_=inputs
    return ['--evaluation',ev,'--code-root',ROOT,'--frozen',frozen,'--original-api',api,
            '--original-offline',offline,'--previous-v43',p43,'--previous-v44',p44,
            '--previous-v45',p45,'--previous-v46',p46,'--previous-v47',p47,'--previous-v48',p48]


def test_pair_prepare_uses_best_measured_parent_and_pins_failed_comparator(inputs49):
    *_,ev,args,before=inputs49
    result=command('prepare_v49.py',args);assert result.returncode==0,result.stderr
    cfg=json.loads((ev/'DEV_PREP_MANIFEST.json').read_text())
    parent=json.loads((inputs49[6]/'DEV_PREP_MANIFEST.json').read_text())
    assert cfg['models']==cfg['parent_v46_models']==parent['models']
    expected=dict(parent['budgets']);expected.update(max_input_tokens=400000,max_provider_requests=36)
    assert cfg['budgets']==expected and cfg['parent_v46_budgets']==parent['budgets']
    assert cfg['nomination_mode']=='none'
    assert cfg['semantic_phase_config']['focused_artifacts_per_request']==3
    assert 'not an equal-compute comparison' in cfg['comparison_note']
    assert cfg['previous_v48']['code_tree_sha256']==PARENT48_HASH
    assert cfg['investigation_profile']=='event-pair-reviewed'
    assert cfg['gold_labels_in_agent_inputs'] is False
    assert 'PRIVATE_GOLD_MARKER' not in ''.join(p.read_text() for p in ev.rglob('*') if p.is_file())
    dry=command('run_v49.py',['--evaluation',ev,'--code-root',ROOT,'--dry-run'])
    assert dry.returncode==0,dry.stderr
    output=json.loads(dry.stdout);assert output['parent_v48_models']==cfg['parent_v48_models']
    assert '--investigation-profile' in output['command'] and 'event-pair-reviewed' in output['command']
    assert output['command'][output['command'].index('--max-provider-requests')+1]=='36'
    assert not (ev/'run').exists() and all(sha(p)==digest for p,digest in before.items())


@pytest.mark.parametrize('relative',['DEV_PREP_MANIFEST.json','run/report.json','inputs/'+HISTORY,
                                    'checkpoints/SIMULATED_V48_NO_PROVIDER.json','score/metrics.json','score/SCORE_RECEIPT.json'])
def test_pair_checks_completed_parent48_before_creation(inputs49,relative):
    p48,ev,args=inputs49[8:11];p=p48/relative;p.write_bytes(p.read_bytes()+b'\n ')
    if relative=='score/SCORE_RECEIPT.json':
        d=json.loads(p.read_text());d['metrics_sha256']='0'*64;write(p,d)
    result=command('prepare_v49.py',args)
    assert result.returncode!=0 and not ev.exists()


@pytest.mark.parametrize('existing',['run','checkpoints','score','RUN_RECEIPT.json','RUN_ATTEMPT.json'])
def test_pair_run_preserves_incomplete_existing_work(inputs49,existing):
    *_,ev,args,_=inputs49
    assert command('prepare_v49.py',args).returncode==0
    p=ev/existing
    if p.suffix:p.write_text('preserve-me')
    else:p.mkdir();p=p/'preserve.txt';p.write_text('preserve-me')
    result=command('run_v49.py',['--evaluation',ev,'--code-root',ROOT,'--dry-run'])
    assert result.returncode!=0 and p.read_text()=='preserve-me'


def test_pair_completed_run_reuse_needs_no_key_and_makes_no_mutation(inputs49,monkeypatch):
    *_,ev,args,before=inputs49
    assert command('prepare_v49.py',args).returncode==0
    complete(ev);monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    original={p:sha(p) for p in ev.rglob('*') if p.is_file()}
    result=command('run_v49.py',['--evaluation',ev,'--code-root',ROOT])
    assert result.returncode==0,result.stderr
    assert 'EXISTING_COMPLETED_RUN_VERIFIED_NO_API_CALLED' in result.stdout
    assert not (ev/'RUN_ATTEMPT.json').exists()
    assert all(sha(p)==value for p,value in original.items())
    assert all(sha(p)==value for p,value in before.items())


def test_pair_changed_completed_checkpoint_cannot_be_reused(inputs49):
    *_,ev,args,_=inputs49
    assert command('prepare_v49.py',args).returncode==0;complete(ev)
    cp=ev/'checkpoints/SIMULATED_V49_NO_PROVIDER.json';cp.write_bytes(cp.read_bytes()+b'\n ')
    result=command('run_v49.py',['--evaluation',ev,'--code-root',ROOT])
    assert result.returncode!=0 and not (ev/'RUN_ATTEMPT.json').exists()


def test_pair_scoring_commits_reuses_and_bundles_all_pins(inputs49):
    *_,ev,args,before=inputs49
    assert command('prepare_v49.py',args).returncode==0
    link={'artifact_id':'synthetic-0','decision_element_id':'synthetic-requirement','relation':'supports'}
    complete(ev,[link,link]);result=command('score_v49.py',scoring_args(inputs49))
    assert result.returncode==0,result.stderr
    m=json.loads((ev/'score/metrics.json').read_text())
    assert m['results']['all']['tp']==1 and m['results']['all']['predicted_exact_triples']==1
    assert m['comparison']['all']['api_v48_dev_f1']==0
    assert m['nominal_budgets']['max_provider_requests']==36
    assert m['semantic_phase_config']['candidate_verification']=='independent'
    original={p:(sha(p),p.stat().st_mtime_ns) for p in (ev/'score').iterdir()}
    result=command('score_v49.py',scoring_args(inputs49))
    assert result.returncode==0 and 'EXISTING_SCORE_VERIFIED_AND_REUSED' in result.stdout
    assert all((sha(p),p.stat().st_mtime_ns)==value for p,value in original.items())
    assert all(sha(p)==value for p,value in before.items())
    zipped=ev/'diagnostics.zip'
    result=command('bundle_v49_diagnostics.py',['--evaluation',ev,'--output',zipped])
    assert result.returncode==0,result.stderr
    with zipfile.ZipFile(zipped) as z:
        assert 'score/SCORE_RECEIPT.json' in z.namelist() and z.testzip() is None


@pytest.mark.parametrize('relative',['score/metrics.json','score/link_errors.csv','score/SCORE_RECEIPT.json'])
def test_pair_changed_score_cannot_be_reused(inputs49,relative):
    *_,ev,args,_=inputs49
    assert command('prepare_v49.py',args).returncode==0;complete(ev)
    assert command('score_v49.py',scoring_args(inputs49)).returncode==0
    p=ev/relative;p.write_bytes(p.read_bytes()+b'\n ')
    if relative=='score/SCORE_RECEIPT.json':
        d=json.loads(p.read_text());d['metrics_sha256']='0'*64;write(p,d)
    preserved=sha(p);result=command('score_v49.py',scoring_args(inputs49))
    assert result.returncode!=0 and sha(p)==preserved


def test_pair_missing_approval_does_not_claim_api_attempt(inputs49):
    *_,ev,args,_=inputs49
    assert command('prepare_v49.py',args).returncode==0
    result=command('run_v49.py',['--evaluation',ev,'--code-root',ROOT])
    assert result.returncode!=0 and 'Hosted calls require' in result.stderr
    assert not (ev/'RUN_ATTEMPT.json').exists()


@pytest.mark.parametrize('field,value',[('max_provider_requests',35),('max_input_tokens',100000)])
def test_pair_changed_experimental_budget_cannot_launch(inputs49,field,value):
    *_,ev,args,_=inputs49
    assert command('prepare_v49.py',args).returncode==0
    cfg=json.loads((ev/'DEV_PREP_MANIFEST.json').read_text());cfg['budgets'][field]=value
    write(ev/'DEV_PREP_MANIFEST.json',cfg)
    result=command('run_v49.py',['--evaluation',ev,'--code-root',ROOT,'--dry-run'])
    assert result.returncode!=0 and 'budget differs' in result.stderr
    assert not (ev/'RUN_ATTEMPT.json').exists()


def test_pair_manifest_provider_limit_must_match_preparation(inputs49):
    *_,ev,args,_=inputs49
    assert command('prepare_v49.py',args).returncode==0;complete(ev)
    manifest=json.loads((ev/'run/manifest.json').read_text());manifest['max_provider_requests']=35
    write(ev/'run/manifest.json',manifest)
    receipt=json.loads((ev/'RUN_RECEIPT.json').read_text());receipt['run_manifest_sha256']=sha(ev/'run/manifest.json')
    write(ev/'RUN_RECEIPT.json',receipt)
    result=command('run_v49.py',['--evaluation',ev,'--code-root',ROOT])
    assert result.returncode!=0 and not (ev/'RUN_ATTEMPT.json').exists()


def test_pair_missing_key_does_not_claim_api_attempt(inputs49,monkeypatch):
    *_,ev,args,_=inputs49
    assert command('prepare_v49.py',args).returncode==0
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    result=command('run_v49.py',['--evaluation',ev,'--code-root',ROOT,'--i-approve-public-repository-excerpts-to-openai'])
    assert result.returncode!=0 and 'OPENAI_API_KEY not found' in result.stderr
    assert not (ev/'RUN_ATTEMPT.json').exists()
