"""Immutable parent/run provenance for the fresh primary-effects experiment."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

from checkpoint_store import CHECKPOINT_POLICY

PARENT_CORE_SHA256 = 'a0e1b1c0156e48d6a4bdae27a02fdfd9e0bedfbdd05bac79c2db812468937b22'
PARENT_HELPER_SHA256 = {
    '_score_core.py': '18553a3a195a490102348e199233ef4ae752efaf8b80e351e52ff354c6d88895',
    'prepare_v49.py': 'abd0f87e12f6024b7bb0611fc1f4ec1b4c80a0f21d68f884118ab708c9c66efb',
    'bundle_v49_diagnostics.py': 'caca031416986a624ebb97daebbd3e3a5d58cc1bcc5e5ba6b9f232b44e029bd2',
}
EXPERIMENT = 'PRIMARY_HUNK_EFFECT_EXPERIMENT'
PROFILE = 'event-primary-effects'
INPUT_NAMES = ['S0_RETROSPECTIVE_RUNTIME.json', 'POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl',
               'BASELINE_README_PINNED.md']
MAX_INPUT_TOKENS = 400000
MAX_PROVIDER_REQUESTS = 24
TOOL_FILES = ['_experiment_common.py', 'baseline_context.py', 'effect_classifier.py',
              'run_primary_effect.py', 'score_primary_effect.py', 'start_primary_effect_no_api.py',
              'checkpoint_store.py']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write('\n')


def toolkit_digest():
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for name in sorted(TOOL_FILES):
        digest.update(name.encode() + b'\0' + bytes.fromhex(sha((root/name).read_bytes())))
    return digest.hexdigest()


def load_code(code_root):
    root = Path(code_root).resolve()
    # The original core digest excludes development_tools. Pin the scorer and
    # provenance helpers separately before importing any of their code.
    for name, expected in PARENT_HELPER_SHA256.items():
        path = root/'development_tools'/name
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != expected:
            raise ValueError('Expected the unchanged original v4.9 helper: ' + name)
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root/'development_tools'))
    from _score_core import code_tree_hash
    if code_tree_hash(root) != PARENT_CORE_SHA256:
        raise ValueError('Expected the unchanged tested v4.9 code root')
    import evorationale
    if Path(evorationale.__file__).resolve().parent.parent != root:
        raise ValueError('A different EvoRationale package is already loaded')
    return root


def verified_parent(code_root, evaluation):
    code_root = load_code(code_root)
    evaluation = Path(evaluation).resolve()
    from bundle_v49_diagnostics import verified_members
    from evorationale.model import validate_state, normalize_history
    members, hashes, run_id = verified_members(evaluation)
    if not {'score/metrics.json', 'score/link_errors.csv'}.issubset(members):
        raise ValueError('Score the original v4.9 run before preparing a primary-effect experiment')
    config = json.loads(members['DEV_PREP_MANIFEST.json'])
    if config.get('v49_python_sha256') != PARENT_CORE_SHA256:
        raise ValueError('Parent was not the pinned v4.9 source')
    checkpoint_name = 'checkpoints/' + run_id + '.json'
    state = validate_state(json.loads(members['inputs/' + INPUT_NAMES[0]]))
    history = normalize_history([json.loads(line) for line in
        members['inputs/' + INPUT_NAMES[1]].decode('utf-8-sig').splitlines() if line.strip()])
    return {'code_root': code_root, 'evaluation': evaluation, 'members': members, 'hashes': hashes,
            'run_id': run_id, 'config': config, 'checkpoint_name': checkpoint_name,
            'checkpoint': json.loads(members[checkpoint_name]), 'state': state, 'history': history}


def assert_parent_unchanged(parent):
    current = verified_parent(parent['code_root'], parent['evaluation'])
    if current['hashes'] != parent['hashes']:
        raise ValueError('Source v4.9 evaluation changed during the experiment')


def output_snapshot(evaluation, code_root):
    """Verify an immutable API attempt, including preserved partial diagnostics."""
    load_code(code_root)
    root = Path(evaluation).resolve()
    data, hashes = {}, {}
    def snapshot(name, expected=None):
        path = root/name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Missing/nonregular experiment member: ' + name)
        raw = path.read_bytes()
        if expected is not None and sha(raw) != expected:
            raise ValueError('Experiment member hash mismatch: ' + name)
        data[name], hashes[name] = raw, sha(raw)
        return raw
    def document(name, expected=None):
        value = json.loads(snapshot(name, expected))
        if not isinstance(value, dict):
            raise ValueError('Expected experiment JSON object: ' + name)
        return value
    receipt = document('RUN_RECEIPT.json')
    if (receipt.get('status') != EXPERIMENT + '_COMPLETED_AND_HASHED'
            or receipt.get('mode') != 'api' or receipt.get('experiment_kind') != EXPERIMENT):
        raise ValueError('Expected a completed real primary-effect API attempt')
    protocol = document('PROTOCOL.json', receipt['protocol_sha256'])
    if (protocol.get('experiment_kind') != EXPERIMENT or protocol.get('mode') != 'api'
            or protocol.get('toolkit_sha256') != toolkit_digest()
            or receipt.get('toolkit_sha256') != protocol.get('toolkit_sha256')
            or receipt.get('source_run_id') != protocol.get('source_run_id')
            or protocol.get('source_core_sha256') != PARENT_CORE_SHA256
            or receipt.get('model') != protocol.get('model')
            or protocol.get('prediction_unit') != 'ONE_PRIMARY_RELATION_TYPE_PER_HUNK_WITH_PRIMARY_TARGET_IDS'
            or protocol.get('secondary_relations_scored') is not False
            or protocol.get('independent_semantic_critic') is not False
            or protocol.get('gold_labels_in_agent_inputs') is not False
            or protocol.get('checkpoint_write_policy') != CHECKPOINT_POLICY
            or protocol.get('new_budget') != {'max_input_tokens': MAX_INPUT_TOKENS,
                                             'max_provider_requests': MAX_PROVIDER_REQUESTS}):
        raise ValueError('Primary-effect protocol mismatch')
    from evorationale.model import validate_state
    from baseline_context import build_baseline_context
    state = validate_state(document('inputs/'+INPUT_NAMES[0], protocol['runtime_s0_sha256']))
    snapshot('inputs/'+INPUT_NAMES[1], protocol['history_sha256'])
    baseline_raw = snapshot('inputs/'+INPUT_NAMES[2], protocol['baseline_readme_sha256'])
    if build_baseline_context(state, baseline_raw) != protocol['baseline_context']:
        raise ValueError('Pinned baseline context reconstruction mismatch')
    run_id = receipt.get('run_id')
    if not isinstance(run_id, str) or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', run_id) is None:
        raise ValueError('Unsafe experiment run ID')
    report = document('run/report.json', receipt['run_report_sha256'])
    manifest = document('run/manifest.json', receipt['run_manifest_sha256'])
    checkpoint_name = 'checkpoints/'+run_id+'.json'
    if receipt.get('checkpoint_relative_path') != checkpoint_name:
        raise ValueError('Primary-effect checkpoint path mismatch')
    checkpoint = document(checkpoint_name, receipt['checkpoint_sha256'])
    if (checkpoint.get('run_id') != run_id or checkpoint.get('initial_state') != state
            or checkpoint.get('report') != report or checkpoint.get('verified_links') != report.get('verified_evidence')
            or report.get('run_id') != run_id or report.get('source_run_id') != protocol['source_run_id']
            or report.get('experiment_kind') != EXPERIMENT or report.get('investigation_profile') != PROFILE
            or report.get('mode') != 'api' or report.get('model') != protocol['model']
            or report.get('secondary_effects_scored') is not False
            or report.get('independent_semantic_critic') is not False
            or report.get('architecture_outcome') != 'NOT_EVALUATED'
            or manifest.get('run_id') != run_id or manifest.get('source_run_id') != protocol['source_run_id']
            or manifest.get('experiment_kind') != EXPERIMENT or manifest.get('investigation_profile') != PROFILE
            or manifest.get('mode') != 'api' or manifest.get('protocol_sha256') != receipt['protocol_sha256']
            or manifest.get('report_sha256') != receipt['run_report_sha256']):
        raise ValueError('Primary-effect report/checkpoint provenance mismatch')
    usage = report['budget_usage']
    if (usage.get('max_provider_requests') != MAX_PROVIDER_REQUESTS
            or usage.get('provider_requests_reserved', MAX_PROVIDER_REQUESTS+1) > MAX_PROVIDER_REQUESTS
            or usage.get('estimated_input_tokens', MAX_INPUT_TOKENS+1) > MAX_INPUT_TOKENS):
        raise ValueError('Primary-effect run exceeded its bounds')
    by_artifact = {}
    for link in report['verified_evidence']:
        by_artifact.setdefault(link['artifact_key'], set()).add(link['relation'])
        if link.get('prediction_projection') != 'PRIMARY_HUNK_EFFECT':
            raise ValueError('A secondary/unprojected effect entered scored output')
    if any(len(relations) != 1 for relations in by_artifact.values()):
        raise ValueError('Multiple primary relation types for an artifact')
    if (root/'score').exists():
        if not report['coverage']['planned_review_complete']:
            raise ValueError('Incomplete classification cannot have a committed accuracy score')
        score_receipt = document('score/SCORE_RECEIPT.json')
        metrics = document('score/metrics.json', score_receipt['metrics_sha256'])
        snapshot('score/link_errors.csv', score_receipt['link_errors_sha256'])
        if (score_receipt.get('status') != EXPERIMENT + '_SCORE_COMMITTED'
                or score_receipt.get('run_report_sha256') != receipt['run_report_sha256']
                or metrics.get('status') != 'PRIMARY_EFFECT_DEVELOPMENT_POST_RUN_REFERENCE_COMPARISON'
                or metrics.get('experiment_kind') != EXPERIMENT or metrics.get('run_id') != run_id
                or metrics.get('source_run_id') != protocol['source_run_id']
                or metrics.get('toolkit_sha256') != protocol['toolkit_sha256']
                or metrics.get('run_report_sha256') != receipt['run_report_sha256']
                or metrics.get('frozen_manifest_sha256') != protocol['frozen_manifest_sha256']
                or metrics.get('frozen_s0_sha256') != protocol['frozen_s0_sha256']):
            raise ValueError('Primary-effect score provenance mismatch')
    return data, hashes, receipt, protocol, report


