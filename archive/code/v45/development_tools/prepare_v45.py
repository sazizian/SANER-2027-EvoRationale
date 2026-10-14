#!/usr/bin/env python3
"""Prepare a fresh v4.5 development run from EXACT original unlabeled inputs.

Only digests of private references are checked; no label rows are copied to agent
inputs. This command never contacts a provider or changes previous experiments.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from _score_core import code_tree_hash, digest, matches, read

DECISION = 'S0_RETROSPECTIVE_RUNTIME.json'
HISTORY = 'POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl'
PARENT_V44_CODE_SHA256 = '9c7fc66afd6d315c5f02a7b4d88a10ca91c7ad43360fadba9d01cd3e71f91e3e'
PARENT_V43_CODE_SHA256 = 'b53989d04604b68d76eddd92412db89b0b33025637e42649abda27714ee53d94'
PARENT_V42_CODE_SHA256 = 'ab892cc339348fc6db243ecbdb18cb6df3a4959d5636332d5f2cdb7945fbdd09'
EXPECTED_V45_CODE_SHA256 = 'e53412024165759b0dec7c6e45556f6857fca39674faf119acf1290f512f5afd'
KIND = 'DEVELOPMENT_ONLY_V45_EVENT_DELTA_COMPARISON'
PROFILE = 'event-delta'
NOMINATION_MODE = 'none'
BUDGET_KEYS = {'max_rounds', 'max_queries', 'max_reads', 'max_input_tokens'}
COMPARISON_NOTE = ('Descriptive development comparison: identical source inputs and nominal budgets; '
                   'investigation profile, judge model, provider-call pattern, and token accounting differ.')
MODEL_CHANGE_NOTE = ('The independent classifier uses the v4.4 linker model instead of the v4.4 judge model. '
                     'By default each event batch is independently classified without a hosted nomination '
                     'call (one classification request before any retry). The copied linker-model field '
                     'remains for optional hosted nomination compatibility. '
                     'This deliberate model change is not an equal-model or equal-compute comparison.')


def save(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')


def validate_configuration(models, budgets):
    if (not isinstance(models, dict) or set(models) != {'linker', 'judge'}
            or any(not isinstance(v, str) or not v.strip() for v in models.values())):
        raise ValueError('Invalid opaque model IDs')
    if (not isinstance(budgets, dict) or not BUDGET_KEYS.issubset(budgets)
            or any(type(budgets[k]) is not int or budgets[k] <= 0 for k in BUDGET_KEYS)):
        raise ValueError('Expected positive integer nominal budgets')


def pin_previous(parent: Path, version: int, expected_hash: str, original: dict, frozen_s0_sha256: str):
    config = read(parent/'DEV_PREP_MANIFEST.json')
    receipt = read(parent/'RUN_RECEIPT.json')
    expected_kind = ('DEVELOPMENT_ONLY_V44_EVENT_COMPLETE_COMPARISON' if version == 44
                     else f'DEVELOPMENT_ONLY_V{version}_CONTROLLED_COMPARISON')
    if (config.get('kind') != expected_kind
            or receipt.get('status') != f'V{version}_DEV_HOSTED_RUN_COMPLETED_AND_HASHED'
            or receipt.get('mode') != 'api'
            or config.get(f'v{version}_python_sha256') != expected_hash
            or receipt.get('code_tree_sha256') != expected_hash):
        raise ValueError(f'Previous v{version/10:.1f} is not the completed pinned development run')
    if version == 44 and (config.get('investigation_profile') != 'event-complete'
                          or receipt.get('investigation_profile') != 'event-complete'):
        raise ValueError('Previous v4.4 event-complete profile mismatch')
    matches(parent/'DEV_PREP_MANIFEST.json', receipt['prep_sha256'], 'previous preparation/configuration')
    matches(parent/'run'/'manifest.json', receipt['run_manifest_sha256'], 'previous run manifest')
    matches(parent/'run'/'report.json', receipt['run_report_sha256'], 'previous report')
    matches(parent/'inputs'/DECISION, original['runtime_s0_sha256'], 'previous identical runtime S0')
    matches(parent/'inputs'/HISTORY, original['history_sha256'], 'previous identical history')
    manifest = read(parent/'run'/'manifest.json')
    if (manifest.get('mode') != 'api' or manifest.get('run_id') != receipt.get('run_id')
            or manifest.get('decision_sha256') != original['runtime_s0_sha256']
            or manifest.get('history_sha256') != original['history_sha256']
            or manifest.get('report_sha256') != receipt['run_report_sha256']):
        raise ValueError('Previous run manifest provenance mismatch')
    if version == 44 and manifest.get('investigation_profile') != 'event-complete':
        raise ValueError('Previous v4.4 run manifest profile mismatch')
    if (config.get('frozen_s0_sha256') != frozen_s0_sha256
            or config.get('frozen_manifest_sha256') != original['frozen_manifest_sha256']
            or config.get('runtime_s0_sha256') != original['runtime_s0_sha256']
            or config.get('history_sha256') != original['history_sha256']
            or receipt.get('model') != config.get('models')):
        raise ValueError('Previous inputs, reference, or models mismatch')
    validate_configuration(config.get('models'), config.get('budgets'))
    if version == 44 and receipt.get('nominal_budgets') != config['budgets']:
        raise ValueError('Previous v4.4 nominal budget receipt mismatch')
    metrics = read(parent/'score'/'metrics.json')
    if (metrics.get('frozen_s0_sha256') != frozen_s0_sha256
            or metrics.get(f'v{version}_run_report_sha256') != receipt['run_report_sha256']):
        raise ValueError('Previous score provenance mismatch')
    pinned = {
        'receipt_sha256': digest(parent/'RUN_RECEIPT.json'),
        'config_sha256': receipt['prep_sha256'],
        'run_manifest_sha256': receipt['run_manifest_sha256'],
        'report_sha256': receipt['run_report_sha256'],
        'score_sha256': digest(parent/'score'/'metrics.json'),
        'runtime_s0_sha256': original['runtime_s0_sha256'],
        'history_sha256': original['history_sha256'],
        'code_tree_sha256': expected_hash,
        'run_id': receipt['run_id'],
    }
    return config, pinned


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original-api', type=Path, required=True)
    p.add_argument('--original-offline', type=Path, required=True)
    p.add_argument('--frozen', type=Path, required=True)
    p.add_argument('--code-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--previous-v43', type=Path, required=True,
                   help='Completed v4.3 descriptive comparator')
    p.add_argument('--previous-v44', type=Path, required=True,
                   help='Completed v4.4 input/model/budget source and primary descriptive comparator')
    p.add_argument('--previous-v42', type=Path, help='Optional additional pinned descriptive comparison')
    a = p.parse_args()
    original, offline, frozen, code, out = (v.resolve() for v in
                                            (a.original_api, a.original_offline, a.frozen, a.code_root, a.output))
    if out.exists():
        raise FileExistsError(f'No overwriting development experiment: {out}')
    prev = read(original/'PREP_MANIFEST.json')
    cfg = read(original/'API_CONFIG.json')
    receipt = read(original/'RUN_RECEIPT.json')
    fm = read(frozen/'FREEZE_MANIFEST.json')
    if receipt.get('status') != 'HOSTED_MODEL_RUN_COMPLETED_AND_HASHED':
        raise ValueError('Original v4.1 hosted run is not completed')
    matches(original/'PREP_MANIFEST.json', receipt['prep_manifest_sha256'], 'original API preparation')
    matches(original/'API_CONFIG.json', receipt['api_config_sha256'], 'original API configuration')
    matches(original/'run'/'report.json', receipt['run_report_sha256'], 'original API run')
    matches(frozen/'FREEZE_MANIFEST.json', prev['frozen_manifest_sha256'], 'reference freeze manifest')
    matches(frozen/'S0_ATOMIC_REVIEWER_CONFIRMED.json', fm['s0_sha256'], 'frozen S0')
    if prev['frozen_s0_sha256'] != fm['s0_sha256']:
        raise ValueError('Original API did not use the same frozen S0')
    for name, value in fm['reference_sha256'].items():
        matches(frozen/'reference'/name, value, 'frozen reference '+name)
    source_decision, source_history = original/'inputs'/DECISION, original/'inputs'/HISTORY
    matches(source_decision, prev['runtime_s0_sha256'], 'original runtime S0')
    matches(source_history, prev['history_sha256'], 'original unlabeled history')
    off = read(offline/'PREP_MANIFEST.json')
    if (off['runtime_s0_sha256'] != prev['runtime_s0_sha256']
            or off['history_sha256'] != prev['history_sha256']):
        raise ValueError('Original offline and API inputs were not identical')
    matches(offline/'score'/'metrics.json', prev['baseline_score_sha256'], 'original offline score')
    if cfg.get('protocol') != 'PRESPECIFIED_RETROSPECTIVE_API_DEVELOPMENT_COMPARISON':
        raise ValueError('Unexpected original API configuration')
    original_metrics = read(original/'score'/'metrics.json')
    if original_metrics.get('run_sha256') != receipt['run_report_sha256']:
        raise ValueError('Original API metrics do not match recorded report')
    code_sha256 = code_tree_hash(code)
    if code_sha256 != EXPECTED_V45_CODE_SHA256:
        raise ValueError('The v4.5-dev source differs from the tested package')
    if not (code/'tests'/'test_v45_development_tools.py').is_file():
        raise ValueError('Not a verified v4.5 development package')
    _, pinned43 = pin_previous(a.previous_v43.resolve(), 43, PARENT_V43_CODE_SHA256, prev, fm['s0_sha256'])
    parent44_cfg, pinned44 = pin_previous(a.previous_v44.resolve(), 44, PARENT_V44_CODE_SHA256, prev, fm['s0_sha256'])
    if parent44_cfg.get('previous_v43') != pinned43:
        raise ValueError('Previous v4.4 did not pin the supplied v4.3 comparison')
    pinned42 = None
    if a.previous_v42 is not None:
        _, pinned42 = pin_previous(a.previous_v42.resolve(), 42, PARENT_V42_CODE_SHA256, prev, fm['s0_sha256'])
    # All provenance checks precede creating the fresh destination.
    out.mkdir(parents=True)
    (out/'inputs').mkdir()
    shutil.copyfile(source_decision, out/'inputs'/DECISION)
    shutil.copyfile(source_history, out/'inputs'/HISTORY)
    config = {
        'kind': KIND, 'models': {'linker': parent44_cfg['models']['linker'],
                                'judge': parent44_cfg['models']['linker']},
        'parent_v44_models': dict(parent44_cfg['models']), 'model_change_note': MODEL_CHANGE_NOTE,
        'budgets': dict(parent44_cfg['budgets']),
        'investigation_profile': PROFILE, 'nomination_mode': NOMINATION_MODE, 'comparison_note': COMPARISON_NOTE,
        'source_v41_python_sha256': prev['evorationale_python_tree_sha256'],
        'v45_python_sha256': code_sha256, 'parent_v43_python_sha256': PARENT_V43_CODE_SHA256,
        'parent_v44_python_sha256': PARENT_V44_CODE_SHA256,
        'previous_v44': pinned44, 'previous_v43': pinned43, 'previous_v42': pinned42,
        'frozen_s0_sha256': fm['s0_sha256'], 'frozen_manifest_sha256': digest(frozen/'FREEZE_MANIFEST.json'),
        'runtime_s0_sha256': digest(out/'inputs'/DECISION), 'history_sha256': digest(out/'inputs'/HISTORY),
        'original_api_report_sha256': receipt['run_report_sha256'],
        'original_api_prep_sha256': digest(original/'PREP_MANIFEST.json'),
        'original_api_config_sha256': digest(original/'API_CONFIG.json'),
        'original_api_score_sha256': digest(original/'score'/'metrics.json'),
        'original_offline_score_sha256': digest(offline/'score'/'metrics.json'),
        'historical_replay_certified': False, 'gold_decision_outcomes_available': False,
        'gold_labels_in_agent_inputs': False, 'creation_utc': datetime.now(timezone.utc).isoformat(),
        'warnings': [
            'Reference examples have been inspected during development; NOT held-out evaluation.',
            COMPARISON_NOTE,
            MODEL_CHANGE_NOTE,
            'Opaque model IDs are reused; immutable model snapshots are not verified.',
            'This preparation does not estimate F1 or invoke a provider. Hosted runs may cost money.',
        ],
    }
    save(out/'DEV_PREP_MANIFEST.json', config)
    print(json.dumps({'status': 'READY_FOR_V45_DEVELOPMENT_ONLY_NO_API_CALLED',
                      'same_runtime_s0': True, 'same_53_artifacts': True, 'gold_labels_in_agent_inputs': False,
                      'investigation_profile': PROFILE, 'comparison_note': COMPARISON_NOTE,
                      'nomination_mode': NOMINATION_MODE,
                      'v41_code_sha256': config['source_v41_python_sha256'],
                      'v45_code_sha256': code_sha256, 'output': str(out)}, indent=2))


if __name__ == '__main__':
    main()
