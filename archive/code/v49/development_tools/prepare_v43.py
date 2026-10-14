#!/usr/bin/env python3
"""Prepare a fresh v4.3 development run from v4.1's EXACT unlabeled inputs.

Copies no human gold labels into the new evaluation directory. Does not call API.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from _score_core import digest, read, code_tree_hash, matches

DECISION = 'S0_RETROSPECTIVE_RUNTIME.json'
HISTORY = 'POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl'
PARENT_V42_CODE_SHA256 = 'ab892cc339348fc6db243ecbdb18cb6df3a4959d5636332d5f2cdb7945fbdd09'
EXPECTED_V43_CODE_SHA256 = 'b53989d04604b68d76eddd92412db89b0b33025637e42649abda27714ee53d94'


def save(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original-api', type=Path, required=True)
    p.add_argument('--original-offline', type=Path, required=True)
    p.add_argument('--frozen', type=Path, required=True)
    p.add_argument('--code-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--models-from-evaluation', type=Path,
                   help='Reuse the exact opaque model IDs from a completed v4.2 development run')
    a = p.parse_args()
    original = a.original_api.resolve()
    offline = a.original_offline.resolve()
    frozen = a.frozen.resolve()
    code = a.code_root.resolve()
    out = a.output.resolve()
    if out.exists():
        raise FileExistsError(f'No overwriting development experiment: {out}')
    prev = read(original/'PREP_MANIFEST.json')
    cfg = read(original/'API_CONFIG.json')
    r = read(original/'RUN_RECEIPT.json')
    fm = read(frozen/'FREEZE_MANIFEST.json')
    if r['status'] != 'HOSTED_MODEL_RUN_COMPLETED_AND_HASHED':
        raise ValueError('Original v4.1 hosted run is not completed')
    matches(original/'PREP_MANIFEST.json', r['prep_manifest_sha256'], 'original API preparation')
    matches(original/'API_CONFIG.json', r['api_config_sha256'], 'original API configuration')
    matches(original/'run'/'report.json', r['run_report_sha256'], 'original API run')
    matches(frozen/'FREEZE_MANIFEST.json', prev['frozen_manifest_sha256'], 'reference freeze manifest')
    matches(frozen/'S0_ATOMIC_REVIEWER_CONFIRMED.json', fm['s0_sha256'], 'frozen S0')
    if prev['frozen_s0_sha256'] != fm['s0_sha256']:
        raise ValueError('Original API did not use the same frozen S0')
    for name, sha in fm['reference_sha256'].items():
        matches(frozen/'reference'/name, sha, 'frozen reference '+name)
    source_decision = original/'inputs'/DECISION
    source_history = original/'inputs'/HISTORY
    matches(source_decision, prev['runtime_s0_sha256'], 'original runtime S0')
    matches(source_history, prev['history_sha256'], 'original unlabeled evidence')
    off = read(offline/'PREP_MANIFEST.json')
    if off['runtime_s0_sha256'] != prev['runtime_s0_sha256'] or off['history_sha256'] != prev['history_sha256']:
        raise ValueError('Original offline and hosted API inputs were not identical')
    matches(offline/'score'/'metrics.json', prev['baseline_score_sha256'], 'original offline score')
    if cfg.get('protocol') != 'PRESPECIFIED_RETROSPECTIVE_API_DEVELOPMENT_COMPARISON':
        raise ValueError('Unexpected original API configuration')
    version_hash = code_tree_hash(code)
    if version_hash != EXPECTED_V43_CODE_SHA256:
        raise ValueError('The v4.3-dev source code differs from the locally tested package')
    if version_hash == prev['evorationale_python_tree_sha256']:
        raise ValueError('Development source unexpectedly identical to v4.1')
    if not (code/'tests'/'test_v43_diff_scope.py').is_file():
        raise ValueError('Not a verified v4.3-dev package')
    model_ids = {'linker': cfg['linker_model'], 'judge': cfg['judge_model']}
    previous_v42 = None
    if a.models_from_evaluation is not None:
        parent = a.models_from_evaluation.resolve()
        parent_cfg = read(parent/'DEV_PREP_MANIFEST.json')
        parent_receipt = read(parent/'RUN_RECEIPT.json')
        if (parent_cfg.get('kind') != 'DEVELOPMENT_ONLY_V42_CONTROLLED_COMPARISON'
                or parent_receipt.get('status') != 'V42_DEV_HOSTED_RUN_COMPLETED_AND_HASHED'
                or parent_receipt.get('mode') != 'api'
                or parent_cfg.get('v42_python_sha256') != PARENT_V42_CODE_SHA256
                or parent_receipt.get('code_tree_sha256') != PARENT_V42_CODE_SHA256):
            raise ValueError('Model source is not the completed pinned v4.2 development run')
        matches(parent/'DEV_PREP_MANIFEST.json', parent_receipt['prep_sha256'], 'v4.2 preparation')
        matches(parent/'run'/'manifest.json', parent_receipt['run_manifest_sha256'], 'v4.2 run manifest')
        matches(parent/'run'/'report.json', parent_receipt['run_report_sha256'], 'v4.2 report')
        matches(parent/'inputs'/DECISION, prev['runtime_s0_sha256'], 'v4.2 identical runtime S0')
        matches(parent/'inputs'/HISTORY, prev['history_sha256'], 'v4.2 identical history')
        if parent_cfg.get('frozen_s0_sha256') != fm['s0_sha256']:
            raise ValueError('v4.2 and v4.3 references differ')
        if (parent_receipt.get('model') != parent_cfg.get('models')
                or set(parent_cfg.get('models', {})) != {'linker', 'judge'}
                or any(not isinstance(value, str) or not value.strip()
                       for value in parent_cfg['models'].values())):
            raise ValueError('Invalid or mismatched previous model configuration')
        model_ids = dict(parent_cfg['models'])
        previous_v42 = {
            'receipt_sha256': digest(parent/'RUN_RECEIPT.json'),
            'report_sha256': parent_receipt['run_report_sha256'],
            'score_sha256': digest(parent/'score'/'metrics.json'),
            'code_tree_sha256': PARENT_V42_CODE_SHA256,
            'run_id': parent_receipt['run_id'],
        }
    out.mkdir(parents=True)
    (out/'inputs').mkdir()
    shutil.copyfile(source_decision, out/'inputs'/DECISION)
    shutil.copyfile(source_history, out/'inputs'/HISTORY)
    config={
        'kind':'DEVELOPMENT_ONLY_V43_CONTROLLED_COMPARISON',
        'models': model_ids,
        'budgets': cfg['budgets'],
        'source_v41_python_sha256':prev['evorationale_python_tree_sha256'],
        'v43_python_sha256':version_hash,
        'parent_v42_python_sha256':PARENT_V42_CODE_SHA256,
        'previous_v42':previous_v42,
        'frozen_s0_sha256':fm['s0_sha256'],
        'frozen_manifest_sha256':digest(frozen/'FREEZE_MANIFEST.json'),
        'runtime_s0_sha256':digest(out/'inputs'/DECISION),
        'history_sha256':digest(out/'inputs'/HISTORY),
        'original_api_report_sha256':r['run_report_sha256'],
        'original_api_prep_sha256':digest(original/'PREP_MANIFEST.json'),
        'original_offline_score_sha256':digest(offline/'score'/'metrics.json'),
        'historical_replay_certified':False,
        'gold_decision_outcomes_available':False,
        'gold_labels_in_agent_inputs':False,
        'creation_utc':datetime.now(timezone.utc).isoformat(),
        'warnings':['Gold labels have been inspected during development: this is NOT held-out evaluation.',
                    'Diff context and full-element/scope judgment contract changed; no new hosted result yet.',
                    'Model aliases not verified immutable snapshots. New API calls may cost money.'],
    }
    save(out/'DEV_PREP_MANIFEST.json', config)
    print(json.dumps({'status':'READY_FOR_V43_DEVELOPMENT_ONLY_NO_API_CALLED',
                      'same_runtime_s0':True,'same_53_artifacts':True,
                      'gold_labels_in_agent_inputs':False,
                      'v41_code_sha256':config['source_v41_python_sha256'],
                      'v43_code_sha256':version_hash,'output':str(out)}, indent=2))


if __name__ == '__main__':
    main()
