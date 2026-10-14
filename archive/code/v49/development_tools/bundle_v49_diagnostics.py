#!/usr/bin/env python3
"""Bundle one attested v4.9 run locally without model calls or credentials."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evorationale.model import validate_state

from prepare_v49 import DECISION, HISTORY, KIND, PROFILE, SEMANTIC_PHASE_CONFIG, validate_prepared_configuration


def checkpoint_relative_for_run_id(run_id):
    if not isinstance(run_id, str) or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', run_id) is None:
        raise ValueError('Unsafe checkpoint run ID')
    return 'checkpoints/'+run_id+'.json'


def verified_members(evaluation: Path):
    """Read a stable byte snapshot and verify each member against its receipt."""
    members = {}
    hashes = {}
    def snapshot(relative, expected=None):
        path = evaluation/relative
        if path.is_symlink() or not path.is_file():
            raise ValueError('Missing or nonregular diagnostic file: '+relative)
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if expected is not None and digest != expected:
            raise ValueError('Hash mismatch for diagnostic '+relative)
        members[relative], hashes[relative] = data, digest
        return data
    def document(relative, expected=None):
        data = json.loads(snapshot(relative, expected).decode('utf-8-sig'))
        if not isinstance(data, dict):
            raise ValueError('Expected JSON object: '+relative)
        return data

    receipt = document('RUN_RECEIPT.json')
    if (receipt.get('status') != 'V49_DEV_HOSTED_RUN_COMPLETED_AND_HASHED'
            or receipt.get('mode') != 'api' or receipt.get('investigation_profile') != PROFILE):
        raise ValueError('Expected a completed attested v4.9 event-pair-reviewed run')
    config = document('DEV_PREP_MANIFEST.json', receipt['prep_sha256'])
    validate_prepared_configuration(config)
    if (config.get('kind') != KIND or config.get('investigation_profile') != PROFILE
            or receipt.get('code_tree_sha256') != config.get('v49_python_sha256')
            or receipt.get('model') != config.get('models')
            or receipt.get('nominal_budgets') != config.get('budgets')
            or receipt.get('parent_v44_models') != config.get('parent_v44_models')
            or receipt.get('parent_v45_models') != config.get('parent_v45_models')
            or receipt.get('parent_v46_models') != config.get('parent_v46_models')
            or receipt.get('parent_v47_models') != config.get('parent_v47_models')
            or receipt.get('parent_v48_models') != config.get('parent_v48_models')
            or receipt.get('semantic_phase_config') != config.get('semantic_phase_config')
            or config.get('semantic_phase_config') != SEMANTIC_PHASE_CONFIG
            or receipt.get('policy_change_note') != config.get('policy_change_note')):
        raise ValueError('Preparation/receipt provenance mismatch')
    if (config.get('nomination_mode') != 'none'
            or receipt.get('nomination_mode') != config['nomination_mode']):
        raise ValueError('Preparation/receipt nomination mode mismatch')
    manifest = document('run/manifest.json', receipt['run_manifest_sha256'])
    report = document('run/report.json', receipt['run_report_sha256'])
    state = document('inputs/'+DECISION, config['runtime_s0_sha256'])
    snapshot('inputs/'+HISTORY, config['history_sha256'])
    if (manifest.get('run_id') != receipt.get('run_id') or manifest.get('mode') != 'api'
            or manifest.get('investigation_profile') != PROFILE
            or manifest.get('nomination_mode') != config['nomination_mode']
            or manifest.get('max_provider_requests') != config['budgets']['max_provider_requests']
            or manifest.get('decision_sha256') != config['runtime_s0_sha256']
            or manifest.get('history_sha256') != config['history_sha256']
            or manifest.get('report_sha256') != receipt['run_report_sha256']):
        raise ValueError('Run manifest provenance mismatch')
    checkpoint_relative = checkpoint_relative_for_run_id(receipt.get('run_id'))
    if receipt.get('checkpoint_relative_path') != checkpoint_relative:
        raise ValueError('Checkpoint path receipt mismatch')
    checkpoint = document(checkpoint_relative, receipt['checkpoint_sha256'])
    if (checkpoint.get('run_id') != receipt['run_id'] or checkpoint.get('initial_state') != validate_state(state)
            or checkpoint.get('report') != report):
        raise ValueError('Checkpoint payload provenance mismatch')
    score_paths = ['score/metrics.json', 'score/link_errors.csv']
    if any((evaluation/relative).exists() for relative in score_paths):
        metrics = document(score_paths[0])
        snapshot(score_paths[1])
        if (metrics.get('status') != 'V49_DEVELOPMENT_ONLY_POST_RUN_REFERENCE_COMPARISON'
                or metrics.get('v49_run_report_sha256') != receipt['run_report_sha256']
                or metrics.get('v49_code_sha256') != config['v49_python_sha256']
                or metrics.get('frozen_s0_sha256') != config['frozen_s0_sha256']):
            raise ValueError('Optional score provenance mismatch')
        if (metrics.get('nomination_mode') != config['nomination_mode']
                or metrics.get('nominal_budgets') != config['budgets']
                or metrics.get('semantic_phase_config') != SEMANTIC_PHASE_CONFIG):
            raise ValueError('Optional score nomination mode mismatch')
        score_receipt = document('score/SCORE_RECEIPT.json')
        if (score_receipt.get('status') != 'V49_SCORE_COMMITTED'
                or score_receipt.get('run_report_sha256') != receipt['run_report_sha256']
                or score_receipt.get('core_sha256') != config['v49_python_sha256']
                or score_receipt.get('frozen_manifest_sha256') != config['frozen_manifest_sha256']
                or score_receipt.get('metrics_sha256') != hashes[score_paths[0]]
                or score_receipt.get('link_errors_sha256') != hashes[score_paths[1]]):
            raise ValueError('Committed score receipt mismatch')
    return members, hashes, receipt['run_id']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='NEW ZIP path; existing files are never overwritten')
    args = parser.parse_args()
    evaluation, output = args.evaluation.resolve(), args.output.resolve()
    if output.exists():
        raise FileExistsError('Refuse overwriting diagnostic ZIP: '+str(output))
    members, hashes, run_id = verified_members(evaluation)
    bundle_manifest = {
        'status': 'V49_DIAGNOSTICS_VERIFIED_NO_API_CALLED', 'run_id': run_id,
        'created_utc': datetime.now(timezone.utc).isoformat(), 'member_sha256': hashes,
        'note': 'This bundle snapshots a development run; it does not certify held-out performance.',
    }
    if not output.parent.is_dir():
        raise FileNotFoundError('Diagnostic ZIP destination folder does not exist: '+str(output.parent))
    # The exclusive file claim remains effective if two callers pass exists().
    with output.open('xb') as stream:
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for relative in sorted(members):
                archive.writestr(relative, members[relative])
            archive.writestr('DIAGNOSTIC_BUNDLE_MANIFEST.json', json.dumps(bundle_manifest, indent=2)+'\n')
    print(json.dumps({'status': bundle_manifest['status'], 'run_id': run_id,
                      'included_files': len(members), 'output': str(output)}, indent=2))


if __name__ == '__main__':
    main()
