"""Synthetic provenance workflows for repair release; never hosted accuracy."""
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from test_v47_development_tools import (inputs47, command as command47, simulate_completion as complete47,
    ROOT,DECISION,HISTORY,sha,write,inputs46,prepared_v45_inputs,prepared_inputs)

PARENT47_HASH='ef221a718301ba59167360c696b8b22d8e65b0747baf1c41f058aea54a942a23'


def command(script,args):
    if script=='prepare_v48.py':
        wrapper=(f'import sys; sys.path.insert(0,{str(ROOT/"development_tools")!r}); '
                 'import prepare_v48; from _score_core import code_tree_hash; '
                 f'prepare_v48.EXPECTED_V48_CODE_SHA256=code_tree_hash({str(ROOT)!r}); prepare_v48.main()')
        invocation=[sys.executable,'-c',wrapper,*map(str,args)]
    else:invocation=[sys.executable,str(ROOT/'development_tools'/script),*map(str,args)]
    return subprocess.run(invocation,cwd=ROOT,capture_output=True,text=True)


@pytest.fixture
def inputs48(inputs47):
    api,offline,frozen,p43,p44,p45,p46,p47,args47,_=inputs47
    result=command47('prepare_v47.py',args47);assert result.returncode==0,result.stderr
    cfg=json.loads((p47/'DEV_PREP_MANIFEST.json').read_text())
    cfg['v47_python_sha256']=PARENT47_HASH;write(p47/'DEV_PREP_MANIFEST.json',cfg)
    complete47(p47)
    metrics=json.loads((p46/'score/metrics.json').read_text())
    metrics.update(status='V47_DEVELOPMENT_ONLY_POST_RUN_REFERENCE_COMPARISON',
                   v47_code_sha256=PARENT47_HASH,v47_run_report_sha256=sha(p47/'run/report.json'),
                   nomination_mode='none')
    write(p47/'score/metrics.json',metrics)
    (p47/'score/link_errors.csv').write_text('scope,verdict,hunk_id,atomic_s0_id,relation,reference_hunk_relation,temporal_basis\n')
    write(p47/'score/SCORE_RECEIPT.json',{'status':'V47_SCORE_COMMITTED',
        'run_report_sha256':sha(p47/'run/report.json'),'core_sha256':PARENT47_HASH,
        'frozen_manifest_sha256':cfg['frozen_manifest_sha256'],
        'metrics_sha256':sha(p47/'score/metrics.json'),'link_errors_sha256':sha(p47/'score/link_errors.csv')})
    ev=p47.parent/'evaluation48';args=list(args47)
    args[args.index('--output')+1]=ev;args.extend(['--previous-v47',p47])
    before={p:sha(p) for folder in (api,offline,frozen,p43,p44,p45,p46,p47)
            for p in folder.rglob('*') if p.is_file()}
    return api,offline,frozen,p43,p44,p45,p46,p47,ev,args,before


def complete(evaluation,evidence=None):
    from evorationale.model import validate_state
    cfg=json.loads((evaluation/'DEV_PREP_MANIFEST.json').read_text())
    report={'verified_evidence':evidence or [],'verification':{'status':'UNRESOLVED'}}
    write(evaluation/'run/report.json',report)
    run_id='SIMULATED_V48_NO_PROVIDER';relative=f'checkpoints/{run_id}.json'
    write(evaluation/'run/manifest.json',{'run_id':run_id,'mode':'api','investigation_profile':'event-evidence-repair',
        'nomination_mode':'none','decision_sha256':cfg['runtime_s0_sha256'],'history_sha256':cfg['history_sha256'],
        'report_sha256':sha(evaluation/'run/report.json')})
    write(evaluation/relative,{'run_id':run_id,'report':report,
        'initial_state':validate_state(json.loads((evaluation/'inputs'/DECISION).read_text()))})
    write(evaluation/'RUN_RECEIPT.json',{'run_id':run_id,'mode':'api','investigation_profile':'event-evidence-repair',
        'nomination_mode':'none','status':'V48_DEV_HOSTED_RUN_COMPLETED_AND_HASHED',
        'code_tree_sha256':cfg['v48_python_sha256'],'model':cfg['models'],'nominal_budgets':cfg['budgets'],
        **{key:cfg[key] for key in ('parent_v44_models','parent_v45_models','parent_v46_models','parent_v47_models','policy_change_note')},
        'prep_sha256':sha(evaluation/'DEV_PREP_MANIFEST.json'),
        'run_manifest_sha256':sha(evaluation/'run/manifest.json'),'run_report_sha256':sha(evaluation/'run/report.json'),
        'checkpoint_relative_path':relative,'checkpoint_sha256':sha(evaluation/relative)})


def scoring_args(inputs):
    api,offline,frozen,p43,p44,p45,p46,p47,ev,*_=inputs
    return ['--evaluation',ev,'--code-root',ROOT,'--frozen',frozen,'--original-api',api,
            '--original-offline',offline,'--previous-v43',p43,'--previous-v44',p44,
            '--previous-v45',p45,'--previous-v46',p46,'--previous-v47',p47]


def test_repair_prepare_uses_best_measured_parent_and_pins_failed_comparator(inputs48):
    *_,ev,args,before=inputs48
    result=command('prepare_v48.py',args);assert result.returncode==0,result.stderr
    cfg=json.loads((ev/'DEV_PREP_MANIFEST.json').read_text())
    parent=json.loads((inputs48[6]/'DEV_PREP_MANIFEST.json').read_text())
    assert cfg['models']==cfg['parent_v46_models']==parent['models']
    assert cfg['budgets']==parent['budgets'] and cfg['nomination_mode']=='none'
    assert cfg['previous_v47']['code_tree_sha256']==PARENT47_HASH
    assert cfg['investigation_profile']=='event-evidence-repair'
    assert cfg['gold_labels_in_agent_inputs'] is False
    assert 'PRIVATE_GOLD_MARKER' not in ''.join(p.read_text() for p in ev.rglob('*') if p.is_file())
    dry=command('run_v48.py',['--evaluation',ev,'--code-root',ROOT,'--dry-run'])
    assert dry.returncode==0,dry.stderr
    output=json.loads(dry.stdout);assert output['parent_v47_models']==cfg['parent_v47_models']
    assert '--investigation-profile' in output['command'] and 'event-evidence-repair' in output['command']
    assert not (ev/'run').exists() and all(sha(p)==digest for p,digest in before.items())


@pytest.mark.parametrize('relative',['DEV_PREP_MANIFEST.json','run/report.json','inputs/'+HISTORY,
                                    'checkpoints/SIMULATED_V47_NO_PROVIDER.json','score/metrics.json','score/SCORE_RECEIPT.json'])
def test_repair_checks_completed_parent47_before_creation(inputs48,relative):
    p47,ev,args=inputs48[7:10];p=p47/relative;p.write_bytes(p.read_bytes()+b'\n ')
    if relative=='score/SCORE_RECEIPT.json':
        d=json.loads(p.read_text());d['metrics_sha256']='0'*64;write(p,d)
    result=command('prepare_v48.py',args)
    assert result.returncode!=0 and not ev.exists()


@pytest.mark.parametrize('existing',['run','checkpoints','score','RUN_RECEIPT.json','RUN_ATTEMPT.json'])
def test_repair_run_preserves_incomplete_existing_work(inputs48,existing):
    *_,ev,args,_=inputs48
    assert command('prepare_v48.py',args).returncode==0
    p=ev/existing
    if p.suffix:p.write_text('preserve-me')
    else:p.mkdir();p=p/'preserve.txt';p.write_text('preserve-me')
    result=command('run_v48.py',['--evaluation',ev,'--code-root',ROOT,'--dry-run'])
    assert result.returncode!=0 and p.read_text()=='preserve-me'


def test_repair_completed_run_reuse_needs_no_key_and_makes_no_mutation(inputs48,monkeypatch):
    *_,ev,args,before=inputs48
    assert command('prepare_v48.py',args).returncode==0
    complete(ev);monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    original={p:sha(p) for p in ev.rglob('*') if p.is_file()}
    result=command('run_v48.py',['--evaluation',ev,'--code-root',ROOT])
    assert result.returncode==0,result.stderr
    assert 'EXISTING_COMPLETED_RUN_VERIFIED_NO_API_CALLED' in result.stdout
    assert not (ev/'RUN_ATTEMPT.json').exists()
    assert all(sha(p)==value for p,value in original.items())
    assert all(sha(p)==value for p,value in before.items())


def test_repair_changed_completed_checkpoint_cannot_be_reused(inputs48):
    *_,ev,args,_=inputs48
    assert command('prepare_v48.py',args).returncode==0;complete(ev)
    cp=ev/'checkpoints/SIMULATED_V48_NO_PROVIDER.json';cp.write_bytes(cp.read_bytes()+b'\n ')
    result=command('run_v48.py',['--evaluation',ev,'--code-root',ROOT])
    assert result.returncode!=0 and not (ev/'RUN_ATTEMPT.json').exists()


def test_repair_scoring_commits_reuses_and_bundles_all_pins(inputs48):
    *_,ev,args,before=inputs48
    assert command('prepare_v48.py',args).returncode==0
    link={'artifact_id':'synthetic-0','decision_element_id':'synthetic-requirement','relation':'supports'}
    complete(ev,[link,link]);result=command('score_v48.py',scoring_args(inputs48))
    assert result.returncode==0,result.stderr
    m=json.loads((ev/'score/metrics.json').read_text())
    assert m['results']['all']['tp']==1 and m['results']['all']['predicted_exact_triples']==1
    assert m['comparison']['all']['api_v47_dev_f1']==0
    original={p:(sha(p),p.stat().st_mtime_ns) for p in (ev/'score').iterdir()}
    result=command('score_v48.py',scoring_args(inputs48))
    assert result.returncode==0 and 'EXISTING_SCORE_VERIFIED_AND_REUSED' in result.stdout
    assert all((sha(p),p.stat().st_mtime_ns)==value for p,value in original.items())
    assert all(sha(p)==value for p,value in before.items())
    zipped=ev/'diagnostics.zip'
    result=command('bundle_v48_diagnostics.py',['--evaluation',ev,'--output',zipped])
    assert result.returncode==0,result.stderr
    with zipfile.ZipFile(zipped) as z:
        assert 'score/SCORE_RECEIPT.json' in z.namelist() and z.testzip() is None


@pytest.mark.parametrize('relative',['score/metrics.json','score/link_errors.csv','score/SCORE_RECEIPT.json'])
def test_repair_changed_score_cannot_be_reused(inputs48,relative):
    *_,ev,args,_=inputs48
    assert command('prepare_v48.py',args).returncode==0;complete(ev)
    assert command('score_v48.py',scoring_args(inputs48)).returncode==0
    p=ev/relative;p.write_bytes(p.read_bytes()+b'\n ')
    if relative=='score/SCORE_RECEIPT.json':
        d=json.loads(p.read_text());d['metrics_sha256']='0'*64;write(p,d)
    preserved=sha(p);result=command('score_v48.py',scoring_args(inputs48))
    assert result.returncode!=0 and sha(p)==preserved


def test_repair_missing_approval_does_not_claim_api_attempt(inputs48):
    *_,ev,args,_=inputs48
    assert command('prepare_v48.py',args).returncode==0
    result=command('run_v48.py',['--evaluation',ev,'--code-root',ROOT])
    assert result.returncode!=0 and 'Hosted calls require' in result.stderr
    assert not (ev/'RUN_ATTEMPT.json').exists()
