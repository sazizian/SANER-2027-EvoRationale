"""Pinned local v4.7 workflows with simulated receipts, never hosted accuracy."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from test_v46_development_tools import (inputs46, command as command46, simulate_completion as complete46,
                                       ROOT, DECISION, HISTORY, sha, write,
                                       prepared_v45_inputs, prepared_inputs)

PARENT46_HASH = 'a01d6dd7e5016c9224c0184053981eddd6621dcd3c6963edf3b391396d420d1b'


def command(script, args):
    if script == 'prepare_v47.py':
        wrapper = (f'import sys; sys.path.insert(0, {str(ROOT/"development_tools")!r}); '
                   'import prepare_v47; from _score_core import code_tree_hash; '
                   f'prepare_v47.EXPECTED_V47_CODE_SHA256 = code_tree_hash({str(ROOT)!r}); prepare_v47.main()')
        invocation = [sys.executable, '-c', wrapper, *map(str, args)]
    else:
        invocation = [sys.executable, str(ROOT/'development_tools'/script), *map(str, args)]
    return subprocess.run(invocation, cwd=ROOT, capture_output=True, text=True)


@pytest.fixture
def inputs47(inputs46):
    api, offline, frozen, p43, p44, p45, p46, args46, _ = inputs46
    result = command46('prepare_v46.py', args46)
    assert result.returncode == 0, result.stderr
    cfg = json.loads((p46/'DEV_PREP_MANIFEST.json').read_text())
    cfg['v46_python_sha256'] = PARENT46_HASH
    write(p46/'DEV_PREP_MANIFEST.json', cfg)
    complete46(p46)
    metrics = json.loads((p45/'score'/'metrics.json').read_text())
    metrics.update({'status': 'V46_DEVELOPMENT_ONLY_POST_RUN_REFERENCE_COMPARISON',
                    'v46_code_sha256': PARENT46_HASH,
                    'v46_run_report_sha256': sha(p46/'run'/'report.json'), 'nomination_mode': 'none'})
    write(p46/'score'/'metrics.json', metrics)
    (p46/'score'/'link_errors.csv').write_text('scope,verdict,hunk_id,atomic_s0_id,relation,reference_hunk_relation,temporal_basis\n')
    evaluation = p46.parent/'evaluation47'
    args = list(args46)
    args[args.index('--output')+1] = evaluation
    args.extend(['--previous-v46', p46])
    before = {path: sha(path) for folder in (api, offline, frozen, p43, p44, p45, p46)
              for path in folder.rglob('*') if path.is_file()}
    return api, offline, frozen, p43, p44, p45, p46, evaluation, args, before


def simulate_completion(evaluation, evidence=None):
    from evorationale.model import validate_state
    cfg = json.loads((evaluation/'DEV_PREP_MANIFEST.json').read_text())
    report = {'verified_evidence': evidence or [], 'verification': {'status': 'UNRESOLVED'}}
    write(evaluation/'run'/'report.json', report)
    run_id = 'SIMULATED_V47_NO_PROVIDER'
    write(evaluation/'run'/'manifest.json', {
        'run_id': run_id, 'mode': 'api', 'investigation_profile': 'event-grounded',
        'nomination_mode': cfg['nomination_mode'], 'decision_sha256': cfg['runtime_s0_sha256'],
        'history_sha256': cfg['history_sha256'], 'report_sha256': sha(evaluation/'run'/'report.json')})
    relative = f'checkpoints/{run_id}.json'
    write(evaluation/relative, {'run_id': run_id, 'report': report,
                              'initial_state': validate_state(json.loads((evaluation/'inputs'/DECISION).read_text()))})
    write(evaluation/'RUN_RECEIPT.json', {
        'run_id': run_id, 'mode': 'api', 'investigation_profile': 'event-grounded',
        'nomination_mode': cfg['nomination_mode'], 'status': 'V47_DEV_HOSTED_RUN_COMPLETED_AND_HASHED',
        'code_tree_sha256': cfg['v47_python_sha256'], 'model': cfg['models'],
        'parent_v44_models': cfg['parent_v44_models'], 'parent_v45_models': cfg['parent_v45_models'],
        'parent_v46_models': cfg['parent_v46_models'],
        'policy_change_note': cfg['policy_change_note'], 'nominal_budgets': cfg['budgets'],
        'prep_sha256': sha(evaluation/'DEV_PREP_MANIFEST.json'),
        'run_manifest_sha256': sha(evaluation/'run'/'manifest.json'),
        'run_report_sha256': sha(evaluation/'run'/'report.json'),
        'checkpoint_relative_path': relative, 'checkpoint_sha256': sha(evaluation/relative)})


def scoring_args(inputs):
    api, offline, frozen, p43, p44, p45, p46, evaluation, *_ = inputs
    return ['--evaluation', evaluation, '--frozen', frozen, '--code-root', ROOT,
            '--original-api', api, '--original-offline', offline,
            '--previous-v43', p43, '--previous-v44', p44, '--previous-v45', p45, '--previous-v46', p46]


def test_v47_prepare_dryrun_preserves_exact_parent_and_unlabeled_inputs(inputs47):
    *_, evaluation, args, before = inputs47
    result = command('prepare_v47.py', args)
    assert result.returncode == 0, result.stderr
    cfg = json.loads((evaluation/'DEV_PREP_MANIFEST.json').read_text())
    parent = json.loads((inputs47[6]/'DEV_PREP_MANIFEST.json').read_text())
    assert cfg['models'] == cfg['parent_v46_models'] == parent['models']
    assert cfg['budgets'] == parent['budgets'] and cfg['nomination_mode'] == 'none'
    assert cfg['previous_v46']['checkpoint_sha256'] == sha(inputs47[6]/cfg['previous_v46']['checkpoint_relative_path'])
    assert cfg['investigation_profile'] == 'event-grounded' and cfg['gold_labels_in_agent_inputs'] is False
    assert sorted(p.name for p in (evaluation/'inputs').iterdir()) == sorted([DECISION, HISTORY])
    assert 'PRIVATE_GOLD_MARKER' not in ''.join(p.read_text() for p in evaluation.rglob('*') if p.is_file())
    dry = command('run_v47.py', ['--evaluation', evaluation, '--code-root', ROOT, '--dry-run'])
    assert dry.returncode == 0, dry.stderr
    out = json.loads(dry.stdout)
    assert out['investigation_profile'] == 'event-grounded' and out['nomination_mode'] == 'none'
    assert out['parent_v46_models'] == cfg['models']
    assert not (evaluation/'run').exists()
    assert all(sha(p) == digest for p, digest in before.items())


@pytest.mark.parametrize('relative', ['DEV_PREP_MANIFEST.json', 'run/manifest.json', 'run/report.json',
                                     'inputs/'+HISTORY, 'checkpoints/SIMULATED_V46_NO_PROVIDER.json', 'score/metrics.json'])
def test_v47_checks_completed_parent46_before_preparation(inputs47, relative):
    p46, evaluation, args = inputs47[6:9]
    path = p46/relative
    if relative == 'score/metrics.json':
        data = json.loads(path.read_text())
        data['v46_run_report_sha256'] = '0'*64
        write(path, data)
    else:
        path.write_bytes(path.read_bytes()+b'\n ')
    result = command('prepare_v47.py', args)
    assert result.returncode != 0 and not evaluation.exists()


@pytest.mark.parametrize('existing', ['run', 'checkpoints', 'score', 'RUN_RECEIPT.json', 'RUN_ATTEMPT.json'])
def test_v47_run_does_not_overwrite_existing_work(inputs47, existing):
    *_, evaluation, args, _ = inputs47
    assert command('prepare_v47.py', args).returncode == 0
    p = evaluation/existing
    if p.suffix: p.write_text('preserve-me')
    else:
        p.mkdir();p = p/'preserve.txt';p.write_text('preserve-me')
    result = command('run_v47.py', ['--evaluation', evaluation, '--code-root', ROOT, '--dry-run'])
    assert result.returncode != 0 and p.read_text() == 'preserve-me'


def test_v47_score_is_committed_and_reused_without_rewriting(inputs47):
    *_, evaluation, args, before = inputs47
    assert command('prepare_v47.py', args).returncode == 0
    link = {'artifact_id': 'synthetic-0', 'decision_element_id': 'synthetic-requirement', 'relation': 'supports'}
    simulate_completion(evaluation, [link, link])
    result = command('score_v47.py', scoring_args(inputs47))
    assert result.returncode == 0, result.stderr
    m = json.loads((evaluation/'score/metrics.json').read_text())
    assert m['results']['all']['tp'] == 1 and m['results']['all']['predicted_exact_triples'] == 1
    assert m['comparison']['all']['api_v46_dev_f1'] == 0
    assert m['comparison']['all']['delta_v47_minus_v46'] == 1
    original = {p:(sha(p),p.stat().st_mtime_ns) for p in (evaluation/'score').iterdir()}
    reused = command('score_v47.py', scoring_args(inputs47))
    assert reused.returncode == 0 and 'EXISTING_SCORE_VERIFIED_AND_REUSED' in reused.stdout
    assert all((sha(p),p.stat().st_mtime_ns) == value for p,value in original.items())
    assert all(sha(p) == value for p,value in before.items())
    assert not list(evaluation.glob('.v47-score-staging-*'))
    zipped = evaluation/'diagnostics.zip'
    result = command('bundle_v47_diagnostics.py', ['--evaluation', evaluation, '--output', zipped])
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(zipped) as z:
        assert 'score/SCORE_RECEIPT.json' in z.namelist()
        assert z.testzip() is None


@pytest.mark.parametrize('relative', ['score/metrics.json', 'score/link_errors.csv', 'score/SCORE_RECEIPT.json',
                                     'checkpoints/SIMULATED_V47_NO_PROVIDER.json'])
def test_v47_reuse_rejects_changed_score_or_attestation(inputs47, relative):
    *_, evaluation, args, _ = inputs47
    assert command('prepare_v47.py', args).returncode == 0
    simulate_completion(evaluation)
    assert command('score_v47.py', scoring_args(inputs47)).returncode == 0
    p = evaluation/relative
    if p.name == 'SCORE_RECEIPT.json':
        data = json.loads(p.read_text());data['metrics_sha256'] = '0'*64;write(p,data)
    else: p.write_bytes(p.read_bytes()+b'\n ')
    preserved = {q:sha(q) for q in (evaluation/'score').iterdir()}
    result = command('score_v47.py', scoring_args(inputs47))
    assert result.returncode != 0
    assert all(sha(q) == value for q,value in preserved.items())


def test_v47_partial_score_is_preserved(inputs47):
    *_, evaluation, args, _ = inputs47
    assert command('prepare_v47.py', args).returncode == 0
    simulate_completion(evaluation)
    (evaluation/'score').mkdir()
    p = evaluation/'score/metrics.json';p.write_text('partial-output')
    result = command('score_v47.py', scoring_args(inputs47))
    assert result.returncode != 0 and p.read_text() == 'partial-output'
    assert not (evaluation/'score/SCORE_RECEIPT.json').exists()


def test_v47_interrupted_scoring_claim_is_preserved(inputs47):
    *_, evaluation, args, _ = inputs47
    assert command('prepare_v47.py', args).returncode == 0
    simulate_completion(evaluation)
    claim = evaluation/'SCORE_ATTEMPT.json'
    claim.write_text('interrupted-attempt-preserve-me')
    result = command('score_v47.py', scoring_args(inputs47))
    assert result.returncode != 0 and claim.read_text() == 'interrupted-attempt-preserve-me'
    assert not (evaluation/'score').exists()


def test_v47_missing_approval_does_not_claim_or_call_provider(inputs47, monkeypatch):
    *_, evaluation, args, _ = inputs47
    assert command('prepare_v47.py', args).returncode == 0
    result = command('run_v47.py', ['--evaluation', evaluation, '--code-root', ROOT])
    assert result.returncode != 0 and 'Hosted calls require' in result.stderr
    assert not (evaluation/'RUN_ATTEMPT.json').exists()
