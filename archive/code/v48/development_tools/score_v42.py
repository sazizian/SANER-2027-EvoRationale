#!/usr/bin/env python3
"""Post-run exact-triple evaluation of a v4.2 development pilot.

Golden human reference remains private until a completed, hash-checked run exists.
This measures a DEVELOPMENT run, not held-out generalization or architecture decisions.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
from _score_core import read,digest,matches,code_tree_hash,evaluate,EVAL_SCOPES,KNOWN,HUNK_FILE
from prepare_v42 import DECISION,HISTORY,save


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evaluation',type=Path,required=True)
    p.add_argument('--frozen',type=Path,required=True)
    p.add_argument('--code-root',type=Path,required=True)
    p.add_argument('--original-api',type=Path,required=True)
    p.add_argument('--original-offline',type=Path,required=True)
    a=p.parse_args()
    ev=a.evaluation.resolve();frozen=a.frozen.resolve();source=a.original_api.resolve();off=a.original_offline.resolve()
    if (ev/'score').exists():
        raise FileExistsError('Refuse to overwrite existing development scores')
    config=read(ev/'DEV_PREP_MANIFEST.json')
    receipt=read(ev/'RUN_RECEIPT.json')
    if receipt['status']!='V42_DEV_HOSTED_RUN_COMPLETED_AND_HASHED' or receipt['mode']!='api':
        raise ValueError('Missing completed, attested v4.2 development run')
    matches(ev/'DEV_PREP_MANIFEST.json',receipt['prep_sha256'],'v42 preparation')
    if code_tree_hash(a.code_root)!=config['v42_python_sha256'] or receipt['code_tree_sha256']!=config['v42_python_sha256']:
        raise ValueError('v4.2 source tree differs from prepared source')
    matches(ev/'inputs'/DECISION,config['runtime_s0_sha256'],'runtime S0')
    matches(ev/'inputs'/HISTORY,config['history_sha256'],'unlabeled history')
    matches(ev/'run'/'manifest.json',receipt['run_manifest_sha256'],'run manifest')
    rm=read(ev/'run'/'manifest.json')
    matches(ev/'run'/'report.json',receipt['run_report_sha256'],'run report')
    if (rm['decision_sha256']!=config['runtime_s0_sha256'] or rm['history_sha256']!=config['history_sha256']
        or rm.get('mode')!='api' or rm['run_id']!=receipt['run_id']):
        raise ValueError('Run provenance mismatch')
    fm=read(frozen/'FREEZE_MANIFEST.json')
    matches(frozen/'FREEZE_MANIFEST.json',config['frozen_manifest_sha256'],'frozen manifest')
    matches(frozen/'S0_ATOMIC_REVIEWER_CONFIRMED.json',fm['s0_sha256'],'frozen S0')
    if fm['s0_sha256']!=config['frozen_s0_sha256']:
        raise ValueError('Frozen S0 changed')
    for name,sha in fm['reference_sha256'].items():
        matches(frozen/'reference'/name,sha,'frozen reference '+name)
    if config['original_api_prep_sha256']!=digest(source/'PREP_MANIFEST.json'):
        raise ValueError('Original API preparation changed')
    if config['original_api_report_sha256']!=digest(source/'run'/'report.json'):
        raise ValueError('Original v4.1 API run changed')
    if config['original_offline_score_sha256']!=digest(off/'score'/'metrics.json'):
        raise ValueError('Offline baseline changed')
    old_api=read(source/'score'/'metrics.json')
    old_off=read(off/'score'/'metrics.json')
    if old_api.get('run_sha256')!=config['original_api_report_sha256']:
        raise ValueError('Original API metrics do not match recorded report')
    with (frozen/'reference'/HUNK_FILE).open(encoding='utf-8-sig',newline='') as f:
        labels=list(csv.DictReader(f))
    if len(labels)!=30 or len({r['hunk_id'] for r in labels})!=30:
        raise ValueError('Expected exactly 30 distinct hunk labels')
    if any(r['relation_candidate'] not in KNOWN for r in labels):
        raise ValueError('Unexpected gold relation')
    report=read(ev/'run'/'report.json')
    summary={
        'status':'V42_DEVELOPMENT_ONLY_POST_RUN_REFERENCE_COMPARISON',
        'v42_code_sha256':config['v42_python_sha256'],
        'frozen_s0_sha256':fm['s0_sha256'],
        'v42_run_report_sha256':receipt['run_report_sha256'],
        'models':receipt['model'],
        'verified_evidence_links':len(report.get('verified_evidence',[])),
        'verification_status':report.get('verification',{}).get('status'),
        'results':{},'comparison':{},
        'warnings':['NOT held-out: the human reference was examined during v4.2 development.',
                    'v4.2 development changes multiple source modules, including the passage proposer and gate.',
                    'The exact-triple scorer is unchanged; new errors might still be caused by taxonomy disagreements.',
                    'No architecture-outcome gold; historical replay remains uncertified.'],
    }
    errors=[]
    for scope in EVAL_SCOPES:
        result, rows = evaluate(labels,report,scope)
        result['limitations']=[x for x in result['limitations'] if 'offline mode' not in x]
        result['limitations'].extend(['v4.2 developer-modified, not independent held-out evaluation',
                                      'model alias snapshots not verified'])
        summary['results'][scope]=result
        previous_api=old_api['results'][scope]
        previous_offline=old_off['results'][scope]
        for other in [previous_api,previous_offline]:
            if (other['gold_positive_exact_triples']!=result['gold_positive_exact_triples']
                    or other['evaluated_hunks']!=result['evaluated_hunks']):
                raise ValueError('Comparison Gold population changed')
        summary['comparison'][scope]={
            'offline_v41_f1':previous_offline['f1'],
            'api_v41_f1':previous_api['f1'],
            'api_v42_dev_f1':result['f1'],
            'delta_v42_minus_api_v41':round(result['f1']-previous_api['f1'],6),
            'note':'Descriptive difference on previously inspected development examples only'
        }
        errors.extend(rows)
    (ev/'score').mkdir()
    save(ev/'score'/'metrics.json',summary)
    with (ev/'score'/'link_errors.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['scope','verdict','hunk_id','atomic_s0_id','relation',
                                       'reference_hunk_relation','temporal_basis'])
        w.writeheader();w.writerows(errors)
    print(json.dumps({'status':summary['status'],'verified_links':summary['verified_evidence_links'],
                      'comparison':summary['comparison'],'output':str(ev/'score')},indent=2))


if __name__=='__main__':
    main()
