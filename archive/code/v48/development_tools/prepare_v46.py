#!/usr/bin/env python3
"""Prepare a fresh v4.6 development run from EXACT original unlabeled inputs.

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
PARENT_V45_CODE_SHA256 = 'e53412024165759b0dec7c6e45556f6857fca39674faf119acf1290f512f5afd'
EXPECTED_V46_CODE_SHA256 = 'a01d6dd7e5016c9224c0184053981eddd6621dcd3c6963edf3b391396d420d1b'
KIND = 'DEVELOPMENT_ONLY_V46_EVENT_EVIDENCE_COMPARISON'
PROFILE = 'event-evidence'
NOMINATION_MODE = 'none'
BUDGET_KEYS = {'max_rounds', 'max_queries', 'max_reads', 'max_input_tokens'}
COMPARISON_NOTE = ('Descriptive development comparison: identical source inputs, opaque model IDs and nominal budgets as v4.5; '
                   'semantic policy, investigation profile and request/token accounting differ. '
                   'Earlier versions also used different models and call patterns.')
MODEL_CHANGE_NOTE = ('Both linker and judge model IDs are copied exactly from the pinned completed v4.5 run; '
                     'nomination remains none. Immutable provider model snapshots are not verified.')
POLICY_CHANGE_NOTE = ('v4.6 separately assesses post-S0 evidence support and target-local change. '
                      'Unchanged context is not fresh evidence, and specific adopted implementation changes '
                      'can trace to a fixed-S0 mechanism through explicit same-event evidence. '
                      'Fixed S0, frozen labels and the exact-triple scorer remain unchanged.')


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
    if version != 45:
        # Preserve historical comparison pins exactly as v4.5 recorded them.
        from prepare_v45 import pin_previous as legacy_pin_previous
        return legacy_pin_previous(parent, version, expected_hash, original, frozen_s0_sha256)
    from bundle_v45_diagnostics import verified_members as verify_v45
    members, hashes, run_id = verify_v45(parent)
    config = read(parent/'DEV_PREP_MANIFEST.json')
    receipt = read(parent/'RUN_RECEIPT.json')
    if (config.get('v45_python_sha256') != expected_hash
            or receipt.get('code_tree_sha256') != expected_hash
            or config.get('nomination_mode') != 'none'
            or config.get('frozen_s0_sha256') != frozen_s0_sha256
            or config.get('frozen_manifest_sha256') != original['frozen_manifest_sha256']
            or config.get('runtime_s0_sha256') != original['runtime_s0_sha256']
            or config.get('history_sha256') != original['history_sha256']):
        raise ValueError('Previous v4.5 source, frozen reference, inputs or nomination mode mismatch')
    validate_configuration(config.get('models'), config.get('budgets'))
    metrics = read(parent/'score'/'metrics.json')
    if (metrics.get('status') != 'V45_DEVELOPMENT_ONLY_POST_RUN_REFERENCE_COMPARISON'
            or metrics.get('v45_run_report_sha256') != receipt['run_report_sha256']
            or metrics.get('v45_code_sha256') != expected_hash
            or metrics.get('frozen_s0_sha256') != frozen_s0_sha256):
        raise ValueError('Previous v4.5 score provenance mismatch')
    pinned = {'receipt_sha256': hashes['RUN_RECEIPT.json'],
              'config_sha256': hashes['DEV_PREP_MANIFEST.json'],
              'run_manifest_sha256': hashes['run/manifest.json'],
              'report_sha256': hashes['run/report.json'],
              'score_sha256': hashes['score/metrics.json'],
              'runtime_s0_sha256': hashes['inputs/'+DECISION],
              'history_sha256': hashes['inputs/'+HISTORY],
              'checkpoint_relative_path': receipt['checkpoint_relative_path'],
              'checkpoint_sha256': receipt['checkpoint_sha256'],
              'code_tree_sha256': expected_hash, 'run_id': run_id}
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
                   help='Completed v4.4 descriptive comparator')
    p.add_argument('--previous-v45', type=Path, required=True,
                   help='Completed v4.5 input/model/budget source and primary descriptive comparator')
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
    if code_sha256 != EXPECTED_V46_CODE_SHA256:
        raise ValueError('The v4.6-dev source differs from the tested package')
    if not (code/'tests'/'test_v46_development_tools.py').is_file():
        raise ValueError('Not a verified v4.6 development package')
    _, pinned43 = pin_previous(a.previous_v43.resolve(), 43, PARENT_V43_CODE_SHA256, prev, fm['s0_sha256'])
    parent44_cfg, pinned44 = pin_previous(a.previous_v44.resolve(), 44, PARENT_V44_CODE_SHA256, prev, fm['s0_sha256'])
    if parent44_cfg.get('previous_v43') != pinned43:
        raise ValueError('Previous v4.4 did not pin the supplied v4.3 comparison')
    parent45_cfg, pinned45 = pin_previous(a.previous_v45.resolve(), 45, PARENT_V45_CODE_SHA256, prev, fm['s0_sha256'])
    if (parent45_cfg.get('previous_v44') != pinned44 or parent45_cfg.get('previous_v43') != pinned43):
        raise ValueError('Previous v4.5 did not pin the supplied v4.4/v4.3 comparisons')
    pinned42 = None
    if a.previous_v42 is not None:
        _, pinned42 = pin_previous(a.previous_v42.resolve(), 42, PARENT_V42_CODE_SHA256, prev, fm['s0_sha256'])
    # All provenance checks precede creating the fresh destination.
    out.mkdir(parents=True)
    (out/'inputs').mkdir()
    shutil.copyfile(source_decision, out/'inputs'/DECISION)
    shutil.copyfile(source_history, out/'inputs'/HISTORY)
    config = {
        'kind': KIND, 'models': dict(parent45_cfg['models']),
        'parent_v44_models': dict(parent44_cfg['models']), 'parent_v45_models': dict(parent45_cfg['models']),
        'model_change_note': MODEL_CHANGE_NOTE, 'policy_change_note': POLICY_CHANGE_NOTE,
        'budgets': dict(parent45_cfg['budgets']),
        'investigation_profile': PROFILE, 'nomination_mode': NOMINATION_MODE, 'comparison_note': COMPARISON_NOTE,
        'source_v41_python_sha256': prev['evorationale_python_tree_sha256'],
        'v46_python_sha256': code_sha256, 'parent_v43_python_sha256': PARENT_V43_CODE_SHA256,
        'parent_v44_python_sha256': PARENT_V44_CODE_SHA256, 'parent_v45_python_sha256': PARENT_V45_CODE_SHA256,
        'previous_v45': pinned45, 'previous_v44': pinned44, 'previous_v43': pinned43, 'previous_v42': pinned42,
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
            MODEL_CHANGE_NOTE, POLICY_CHANGE_NOTE,
            'Opaque model IDs are reused; immutable model snapshots are not verified.',
            'This preparation does not estimate F1 or invoke a provider. Hosted runs may cost money.',
        ],
    }
    save(out/'DEV_PREP_MANIFEST.json', config)
    print(json.dumps({'status': 'READY_FOR_V46_DEVELOPMENT_ONLY_NO_API_CALLED',
                      'same_runtime_s0': True, 'same_53_artifacts': True, 'gold_labels_in_agent_inputs': False,
                      'investigation_profile': PROFILE, 'comparison_note': COMPARISON_NOTE,
                      'nomination_mode': NOMINATION_MODE,
                      'v41_code_sha256': config['source_v41_python_sha256'],
                      'v46_code_sha256': code_sha256, 'output': str(out)}, indent=2))


if __name__ == '__main__':
    main()
