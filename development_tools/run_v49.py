#!/usr/bin/env python3
"""Run a fresh prepared v4.9 development pilot; dry-run never calls a provider."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evorationale.model import validate_state

from _score_core import code_tree_hash, digest, matches, read
from prepare_v49 import COMPARISON_NOTE, DECISION, HISTORY, KIND, MODEL_CHANGE_NOTE, POLICY_CHANGE_NOTE, PROFILE, SEMANTIC_PHASE_CONFIG, save, validate_prepared_configuration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation', type=Path, required=True)
    parser.add_argument('--code-root', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--i-approve-public-repository-excerpts-to-openai', action='store_true')
    args = parser.parse_args()
    ev, code = args.evaluation.resolve(), args.code_root.resolve()
    prep_sha256 = digest(ev/'DEV_PREP_MANIFEST.json')
    config = read(ev/'DEV_PREP_MANIFEST.json')
    if config.get('kind') != KIND or config.get('investigation_profile') != PROFILE:
        raise ValueError('Missing v4.9 event-pair-reviewed preparation')
    validate_prepared_configuration(config)
    if config.get('policy_change_note') != POLICY_CHANGE_NOTE:
        raise ValueError('v4.9 semantic policy differs from the prepared package')
    if config.get('nomination_mode') != 'none':
        raise ValueError('Missing or invalid v4.9 nomination mode')
    matches(ev/'inputs'/DECISION, config['runtime_s0_sha256'], 'runtime S0')
    matches(ev/'inputs'/HISTORY, config['history_sha256'], 'unlabeled history')
    if code_tree_hash(code) != config['v49_python_sha256']:
        raise ValueError('Code changed after development preparation')
    if any((ev/name).exists() for name in ('run', 'checkpoints', 'RUN_RECEIPT.json', 'RUN_ATTEMPT.json', 'score')):
        if (ev/'RUN_RECEIPT.json').is_file():
            from bundle_v49_diagnostics import verified_members
            _, _, existing_run_id = verified_members(ev)
            print(json.dumps({'status': 'V49_EXISTING_COMPLETED_RUN_VERIFIED_NO_API_CALLED',
                              'run_id': existing_run_id, 'output': str(ev/'run'/'report.json')}, indent=2))
            return
        raise FileExistsError('Refuse overwriting existing v4.9 run. Prepare a NEW output directory.')
    budget = config['budgets']
    command = [sys.executable, '-m', 'evorationale', 'run',
               '--decision', str(ev/'inputs'/DECISION), '--history', str(ev/'inputs'/HISTORY),
               '--output', str(ev/'run'), '--mode', 'api', '--allow-repository-text-to-api',
               '--model', config['models']['linker'], '--judge-model', config['models']['judge'],
               '--backend', 'local', '--memory', 'file', '--memory-dir', str(ev/'checkpoints'),
               '--investigation-profile', config['investigation_profile'],
               '--delta-nomination', config['nomination_mode'],
               '--max-rounds', str(budget['max_rounds']), '--max-queries', str(budget['max_queries']),
               '--max-reads', str(budget['max_reads']), '--max-input-tokens', str(budget['max_input_tokens']),
               '--max-provider-requests', str(budget['max_provider_requests'])]
    if args.dry_run:
        print(json.dumps({'status': 'DRY_RUN_NO_API_CALLED', 'model': config['models'], 'budgets': budget,
                          'investigation_profile': PROFILE, 'comparison_note': COMPARISON_NOTE,
                          'nomination_mode': config['nomination_mode'],
                          'parent_v44_models': config['parent_v44_models'], 'parent_v45_models': config['parent_v45_models'],
                          'parent_v46_models': config['parent_v46_models'], 'parent_v47_models': config['parent_v47_models'],
                          'parent_v48_models': config['parent_v48_models'], 'semantic_phase_config': SEMANTIC_PHASE_CONFIG,
        'policy_change_note': POLICY_CHANGE_NOTE, 'model_change_note': MODEL_CHANGE_NOTE,
                          'inputs_hash_match': True, 'command': command}, indent=2))
        return
    if not args.i_approve_public_repository_excerpts_to_openai:
        raise PermissionError('Hosted calls require --i-approve-public-repository-excerpts-to-openai')
    if not os.environ.get('OPENAI_API_KEY'):
        raise RuntimeError('OPENAI_API_KEY not found in environment (do not print the secret)')
    matches(ev/'DEV_PREP_MANIFEST.json', prep_sha256, 'preparation before hosted attempt')
    print('Running v4.9 development pilot: API usage may incur costs.', flush=True)
    began = datetime.now(timezone.utc).isoformat()
    # Claim the prepared evaluation before any provider work. Two launchers can
    # both pass the output-directory check before the agent writes checkpoints.
    # Exclusive creation prevents them from sharing or overwriting that run.
    # Keep this record after an interrupted or failed attempt so the next launch
    # must use a fresh preparation, preserving any partial results.
    try:
        with (ev/'RUN_ATTEMPT.json').open('x', encoding='utf-8') as attempt:
            json.dump({'status': 'V49_HOSTED_ATTEMPT_STARTED', 'start_utc': began,
                       'prep_sha256': prep_sha256,
                       'code_tree_sha256': config['v49_python_sha256']}, attempt, indent=2)
            attempt.write('\n')
    except FileExistsError as exc:
        raise FileExistsError('Refuse overwriting an existing v4.9 run attempt. '
                              'Prepare a NEW output directory.') from exc
    environment = os.environ.copy()
    environment['PYTHONUTF8'] = '1'
    subprocess.run(command, cwd=code, env=environment, check=True)
    # Attest the configuration and bytes that were checked before execution,
    # rather than silently hashing a version edited while the provider ran.
    matches(ev/'DEV_PREP_MANIFEST.json', prep_sha256, 'preparation after hosted attempt')
    matches(ev/'inputs'/DECISION, config['runtime_s0_sha256'], 'runtime S0 after hosted attempt')
    matches(ev/'inputs'/HISTORY, config['history_sha256'], 'history after hosted attempt')
    if code_tree_hash(code) != config['v49_python_sha256']:
        raise ValueError('Code changed during development execution; no completion receipt written')
    manifest = read(ev/'run'/'manifest.json')
    matches(ev/'run'/'report.json', manifest['report_sha256'], 'run report')
    if (manifest.get('mode') != 'api' or manifest.get('investigation_profile') != PROFILE
            or manifest.get('nomination_mode') != config['nomination_mode']
            or manifest.get('max_provider_requests') != budget['max_provider_requests']
            or manifest['decision_sha256'] != config['runtime_s0_sha256']
            or manifest['history_sha256'] != config['history_sha256']):
        raise ValueError('v4.9 run manifest provenance mismatch')
    run_id = manifest.get('run_id')
    if not isinstance(run_id, str) or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', run_id) is None:
        raise ValueError('Unsafe checkpoint run ID')
    checkpoint_relative = 'checkpoints/'+run_id+'.json'
    checkpoint_path = ev/checkpoint_relative
    checkpoint = read(checkpoint_path)
    if (checkpoint.get('run_id') != run_id or checkpoint.get('report') != read(ev/'run'/'report.json')
            or checkpoint.get('initial_state') != validate_state(read(ev/'inputs'/DECISION))):
        raise ValueError('Checkpoint provenance mismatch; no completion receipt written')
    receipt = {
        'status': 'V49_DEV_HOSTED_RUN_COMPLETED_AND_HASHED', 'run_id': manifest['run_id'],
        'start_utc': began, 'finish_utc': datetime.now(timezone.utc).isoformat(),
        'model': config['models'], 'mode': 'api', 'investigation_profile': PROFILE,
        'nomination_mode': config['nomination_mode'],
        'parent_v44_models': config['parent_v44_models'], 'parent_v45_models': config['parent_v45_models'],
        'parent_v46_models': config['parent_v46_models'], 'parent_v47_models': config['parent_v47_models'],
                          'parent_v48_models': config['parent_v48_models'], 'semantic_phase_config': SEMANTIC_PHASE_CONFIG,
        'policy_change_note': POLICY_CHANGE_NOTE, 'model_change_note': MODEL_CHANGE_NOTE,
        'nominal_budgets': config['budgets'],
        'run_report_sha256': manifest['report_sha256'],
        'run_manifest_sha256': digest(ev/'run'/'manifest.json'),
        'checkpoint_relative_path': checkpoint_relative, 'checkpoint_sha256': digest(checkpoint_path),
        'prep_sha256': prep_sha256, 'code_tree_sha256': config['v49_python_sha256'],
        'command_without_credentials': command, 'comparison_note': COMPARISON_NOTE,
        'warning': 'This is a development run; it is not independent held-out evaluation.',
    }
    save(ev/'RUN_RECEIPT.json', receipt)
    print(json.dumps({'status': receipt['status'], 'run_id': receipt['run_id'],
                      'output': str(ev/'run'/'report.json')}, indent=2))


if __name__ == '__main__':
    main()
