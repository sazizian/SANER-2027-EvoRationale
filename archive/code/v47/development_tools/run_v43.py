#!/usr/bin/env python3
"""Execute separately prepared v4.3-dev API run (explicit consent and fail-closed input checks)."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from _score_core import digest, read, code_tree_hash, matches
from prepare_v43 import DECISION, HISTORY, save


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evaluation',type=Path,required=True)
    p.add_argument('--code-root',type=Path,required=True)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--i-approve-public-repository-excerpts-to-openai',action='store_true')
    a=p.parse_args()
    ev=a.evaluation.resolve();code=a.code_root.resolve()
    cfg=read(ev/'DEV_PREP_MANIFEST.json')
    if cfg.get('kind')!='DEVELOPMENT_ONLY_V43_CONTROLLED_COMPARISON':
        raise ValueError('Missing v4.3 preparation')
    matches(ev/'inputs'/DECISION,cfg['runtime_s0_sha256'],'runtime S0')
    matches(ev/'inputs'/HISTORY,cfg['history_sha256'],'unlabeled history')
    if code_tree_hash(code)!=cfg['v43_python_sha256']:
        raise ValueError('Code changed after development preparation')
    if (ev/'run').exists() or (ev/'checkpoints').exists() or (ev/'RUN_RECEIPT.json').exists():
        raise FileExistsError('Refuse overwriting an existing v4.3 run. Prepare a NEW output directory.')
    b=cfg['budgets']
    cmd=[sys.executable,'-m','evorationale','run',
         '--decision',str(ev/'inputs'/DECISION),
         '--history',str(ev/'inputs'/HISTORY),
         '--output',str(ev/'run'),
         '--mode','api','--allow-repository-text-to-api',
         '--model',cfg['models']['linker'], '--judge-model',cfg['models']['judge'],
         '--backend','local','--memory','file','--memory-dir',str(ev/'checkpoints'),
         '--max-rounds',str(b['max_rounds']), '--max-queries',str(b['max_queries']),
         '--max-reads',str(b['max_reads']), '--max-input-tokens',str(b['max_input_tokens'])]
    if a.dry_run:
        print(json.dumps({'status':'DRY_RUN_NO_API_CALLED','model':cfg['models'],
                          'budgets':b,'inputs_hash_match':True,'command':cmd},indent=2))
        return
    if not a.i_approve_public_repository_excerpts_to_openai:
        raise PermissionError('Hosted calls need explicit --i-approve-public-repository-excerpts-to-openai')
    if not os.environ.get('OPENAI_API_KEY'):
        raise RuntimeError('OPENAI_API_KEY not found in environment (do not print secret)')
    print('Running v4.3 development pilot: API usage may incur costs.',flush=True)
    began=datetime.now(timezone.utc).isoformat()
    subprocess.run(cmd,cwd=code,check=True)
    manifest=read(ev/'run'/'manifest.json')
    matches(ev/'run'/'report.json',manifest['report_sha256'],'run report')
    if manifest.get('mode')!='api' or manifest['decision_sha256']!=cfg['runtime_s0_sha256'] or manifest['history_sha256']!=cfg['history_sha256']:
        raise ValueError('v4.3 run manifest provenance mismatch')
    receipt={'status':'V43_DEV_HOSTED_RUN_COMPLETED_AND_HASHED','run_id':manifest['run_id'],
             'start_utc':began,'finish_utc':datetime.now(timezone.utc).isoformat(),
             'model':cfg['models'],'mode':'api','run_report_sha256':manifest['report_sha256'],
             'run_manifest_sha256':digest(ev/'run'/'manifest.json'),
             'prep_sha256':digest(ev/'DEV_PREP_MANIFEST.json'),
             'code_tree_sha256':cfg['v43_python_sha256'],
             'command_without_credentials':cmd,
             'warning':'This development run is not an independent held-out evaluation.'}
    save(ev/'RUN_RECEIPT.json',receipt)
    print(json.dumps({'status':receipt['status'],'run_id':receipt['run_id'],
                      'output':str(ev/'run'/'report.json')},indent=2))


if __name__=='__main__':
    main()
