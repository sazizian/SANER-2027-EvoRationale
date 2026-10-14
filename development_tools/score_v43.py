#!/usr/bin/env python3
"""Post-run exact-triple evaluation of a v4.3 development pilot.

Golden human reference remains private until a completed, hash-checked run exists.
This measures a DEVELOPMENT run, not held-out generalization or architecture decisions.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
from _score_core import read,digest,matches,code_tree_hash,evaluate,EVAL_SCOPES,KNOWN,HUNK_FILE
from prepare_v43 import DECISION,HISTORY,save


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evaluation',type=Path,required=True)
    p.add_argument('--frozen',type=Path,required=True)
    p.add_argument('--code-root',type=Path,required=True)
    p.add_argument('--original-api',type=Path,required=True)
    p.add_argument('--original-offline',type=Path,required=True)
    p.add_argument('--previous-v42',type=Path,
                   help='Optional completed v4.2 run pinned during preparation')
    a=p.parse_args()
    ev=a.evaluation.resolve();frozen=a.frozen.resolve();source=a.original_api.resolve();off=a.original_offline.resolve()
    if (ev/'score').exists():
        raise FileExistsError('Refuse to overwrite existing development scores')
    config=read(ev/'DEV_PREP_MANIFEST.json')
    receipt=read(ev/'RUN_RECEIPT.json')
    if receipt['status']!='V43_DEV_HOSTED_RUN_COMPLETED_AND_HASHED' or receipt['mode']!='api':
        raise ValueError('Missing completed, attested v4.3 development run')
    matches(ev/'DEV_PREP_MANIFEST.json',receipt['prep_sha256'],'v43 preparation')
    if code_tree_hash(a.code_root)!=config['v43_python_sha256'] or receipt['code_tree_sha256']!=config['v43_python_sha256']:
        raise ValueError('v4.3 source tree differs from prepared source')
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
    previous_v42_metrics = None
    if a.previous_v42 is not None:
        parent = a.previous_v42.resolve()
        pinned = config.get('previous_v42')
        if not pinned:
            raise ValueError('No previous v4.2 comparison was pinned during preparation')
        matches(parent/'RUN_RECEIPT.json', pinned['receipt_sha256'], 'previous v4.2 receipt')
        matches(parent/'run'/'report.json', pinned['report_sha256'], 'previous v4.2 report')
        matches(parent/'score'/'metrics.json', pinned['score_sha256'], 'previous v4.2 scores')
        previous_v42_metrics = read(parent/'score'/'metrics.json')
        if (previous_v42_metrics.get('frozen_s0_sha256') != config['frozen_s0_sha256']
                or previous_v42_metrics.get('v42_run_report_sha256') != pinned['report_sha256']):
            raise ValueError('Previous v4.2 score provenance mismatch')
    with (frozen/'reference'/HUNK_FILE).open(encoding='utf-8-sig',newline='') as f:
        labels=list(csv.DictReader(f))
    if len(labels)!=30 or len({r['hunk_id'] for r in labels})!=30:
        raise ValueError('Expected exactly 30 distinct hunk labels')
    if any(r['relation_candidate'] not in KNOWN for r in labels):
        raise ValueError('Unexpected gold relation')
    report=read(ev/'run'/'report.json')
    summary={
        'status':'V43_DEVELOPMENT_ONLY_POST_RUN_REFERENCE_COMPARISON',
        'v43_code_sha256':config['v43_python_sha256'],
        'frozen_s0_sha256':fm['s0_sha256'],
        'v43_run_report_sha256':receipt['run_report_sha256'],
        'models':receipt['model'],
        'verified_evidence_links':len(report.get('verified_evidence',[])),
        'verification_status':report.get('verification',{}).get('status'),
        'results':{},'comparison':{},
        'warnings':['NOT held-out: the human reference was examined during v4.3 development.',
                    'v4.3 development changes multiple source modules, including source-derived diff context and full-element/scope judgment.',
                    'The exact-triple scorer is unchanged; new errors might still be caused by taxonomy disagreements.',
                    'No architecture-outcome gold; historical replay remains uncertified.'],
    }
    errors=[]
    for scope in EVAL_SCOPES:
        result, rows = evaluate(labels,report,scope)
        result['limitations']=[x for x in result['limitations'] if 'offline mode' not in x]
        result['limitations'].extend(['v4.3 developer-modified, not independent held-out evaluation',
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
            'api_v43_dev_f1':result['f1'],
            'delta_v43_minus_api_v41':round(result['f1']-previous_api['f1'],6),
            'note':'Descriptive difference on previously inspected development examples only'
        }
        if previous_v42_metrics is not None:
            previous = previous_v42_metrics['results'][scope]
            if (previous['gold_positive_exact_triples'] != result['gold_positive_exact_triples']
                    or previous['evaluated_hunks'] != result['evaluated_hunks']):
                raise ValueError('v4.2 comparison Gold population changed')
            summary['comparison'][scope]['api_v42_dev_f1'] = previous['f1']
            summary['comparison'][scope]['delta_v43_minus_v42'] = round(result['f1'] - previous['f1'], 6)
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
