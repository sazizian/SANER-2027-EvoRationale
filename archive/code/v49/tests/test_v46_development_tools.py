"""No-provider v4.6 workflows with explicitly simulated receipts, never measured F1."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile
import pytest
from test_v45_development_tools import (
    DECISION, HISTORY, ROOT, command as prior_command, prepared_v45_inputs,
    sha, simulate_v45_completion, write, prepared_inputs,
)
PARENT45_HASH = 'e53412024165759b0dec7c6e45556f6857fca39674faf119acf1290f512f5afd'


def command(script, args):
    if script == 'prepare_v46.py':
        wrapper = (f'import sys; sys.path.insert(0, {str(ROOT/"development_tools")!r}); '
                   'import prepare_v46; from _score_core import code_tree_hash; '
                   f'prepare_v46.EXPECTED_V46_CODE_SHA256 = code_tree_hash({str(ROOT)!r}); prepare_v46.main()')
        invocation = [sys.executable, '-c', wrapper, *map(str, args)]
    else:
        invocation = [sys.executable, str(ROOT/'development_tools'/script), *map(str, args)]
    return subprocess.run(invocation, cwd=ROOT, capture_output=True, text=True)


@pytest.fixture
def inputs46(prepared_v45_inputs):
    api, offline, frozen, p43, p44, p45, args45, _ = prepared_v45_inputs
    result = prior_command('prepare_v45.py', args45)
    assert result.returncode == 0, result.stderr
    cfg = json.loads((p45/'DEV_PREP_MANIFEST.json').read_text())
    cfg['v45_python_sha256'] = PARENT45_HASH
    write(p45/'DEV_PREP_MANIFEST.json', cfg)
    simulate_v45_completion(p45)
    metrics = json.loads((p44/'score'/'metrics.json').read_text())
    metrics.update({'status': 'V45_DEVELOPMENT_ONLY_POST_RUN_REFERENCE_COMPARISON',
                    'v45_code_sha256': PARENT45_HASH,
                    'v45_run_report_sha256': sha(p45/'run'/'report.json'), 'nomination_mode': 'none'})
    write(p45/'score'/'metrics.json', metrics)
    (p45/'score'/'link_errors.csv').write_text('scope,verdict,hunk_id,atomic_s0_id,relation,reference_hunk_relation,temporal_basis\n')
    evaluation = p45.parent/'evaluation46'
    args = list(args45)
    args[args.index('--output')+1] = evaluation
    args.extend(['--previous-v45', p45])
    before = {path: sha(path) for folder in (api, offline, frozen, p43, p44, p45)
              for path in folder.rglob('*') if path.is_file()}
    return api, offline, frozen, p43, p44, p45, evaluation, args, before


def simulate_completion(evaluation, evidence=None):
    from evorationale.model import validate_state
    cfg = json.loads((evaluation/'DEV_PREP_MANIFEST.json').read_text())
    report = {'verified_evidence': evidence or [], 'verification': {'status': 'UNRESOLVED'}}
    write(evaluation/'run'/'report.json', report)
    run_id = 'SIMULATED_V46_NO_PROVIDER'
    write(evaluation/'run'/'manifest.json', {
        'run_id': run_id, 'mode': 'api', 'investigation_profile': 'event-evidence',
        'nomination_mode': cfg['nomination_mode'], 'decision_sha256': cfg['runtime_s0_sha256'],
        'history_sha256': cfg['history_sha256'], 'report_sha256': sha(evaluation/'run'/'report.json')})
    relative = f'checkpoints/{run_id}.json'
    write(evaluation/relative, {'run_id': run_id, 'report': report,
                              'initial_state': validate_state(json.loads((evaluation/'inputs'/DECISION).read_text()))})
    write(evaluation/'RUN_RECEIPT.json', {
        'run_id': run_id, 'mode': 'api', 'investigation_profile': 'event-evidence',
        'nomination_mode': cfg['nomination_mode'], 'status': 'V46_DEV_HOSTED_RUN_COMPLETED_AND_HASHED',
        'code_tree_sha256': cfg['v46_python_sha256'], 'model': cfg['models'],
        'parent_v44_models': cfg['parent_v44_models'], 'parent_v45_models': cfg['parent_v45_models'],
        'policy_change_note': cfg['policy_change_note'], 'nominal_budgets': cfg['budgets'],
        'prep_sha256': sha(evaluation/'DEV_PREP_MANIFEST.json'),
        'run_manifest_sha256': sha(evaluation/'run'/'manifest.json'),
        'run_report_sha256': sha(evaluation/'run'/'report.json'),
        'checkpoint_relative_path': relative, 'checkpoint_sha256': sha(evaluation/relative)})


def scoring_args(inputs):
    api, offline, frozen, p43, p44, p45, evaluation, *_ = inputs
    return ['--evaluation', evaluation, '--frozen', frozen, '--code-root', ROOT,
            '--original-api', api, '--original-offline', offline,
            '--previous-v43', p43, '--previous-v44', p44, '--previous-v45', p45]


def load_tool(name, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'development_tools'))
    spec = importlib.util.spec_from_file_location('test46_'+name, ROOT/'development_tools'/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v46_same_models_budget_inputs_no_api(inputs46):
    *_, evaluation, args, before = inputs46
    result = command('prepare_v46.py', args)
    assert result.returncode == 0, result.stderr
    cfg = json.loads((evaluation/'DEV_PREP_MANIFEST.json').read_text())
    parent = json.loads((inputs46[5]/'DEV_PREP_MANIFEST.json').read_text())
    assert cfg['models'] == cfg['parent_v45_models'] == parent['models']
    assert cfg['budgets'] == parent['budgets'] and cfg['nomination_mode'] == 'none'
    assert cfg['investigation_profile'] == 'event-evidence'
    assert cfg['previous_v45']['checkpoint_sha256'] == sha(inputs46[5]/cfg['previous_v45']['checkpoint_relative_path'])
    assert cfg['gold_labels_in_agent_inputs'] is False
    assert 'PRIVATE_GOLD_MARKER' not in ''.join(p.read_text() for p in evaluation.rglob('*') if p.is_file())
    assert sorted(p.name for p in (evaluation/'inputs').iterdir()) == sorted([DECISION, HISTORY])
    dry = command('run_v46.py', ['--evaluation', evaluation, '--code-root', ROOT, '--dry-run'])
    assert dry.returncode == 0, dry.stderr
    out = json.loads(dry.stdout)
    invocation = out['command']
    assert invocation[invocation.index('--investigation-profile')+1] == 'event-evidence'
    assert invocation[invocation.index('--delta-nomination')+1] == 'none'
    assert out['policy_change_note'] == cfg['policy_change_note']
    assert not (evaluation/'run').exists() and not (evaluation/'RUN_ATTEMPT.json').exists()
    assert all(sha(path) == value for path, value in before.items())


@pytest.mark.parametrize('relative', ['DEV_PREP_MANIFEST.json', 'run/manifest.json', 'run/report.json',
                                     'inputs/'+HISTORY, 'checkpoints/SIMULATED_V45_NO_PROVIDER.json'])
def test_v46_parent45_attestation_before_preparation(inputs46, relative):
    p45, evaluation, args = inputs46[5:8]
    path = p45/relative
    path.write_bytes(path.read_bytes()+b'\n ')
    result = command('prepare_v46.py', args)
    assert result.returncode != 0 and 'Hash mismatch' in result.stderr
    assert not evaluation.exists()


@pytest.mark.parametrize('existing', ['run', 'checkpoints', 'score', 'RUN_RECEIPT.json', 'RUN_ATTEMPT.json'])
def test_v46_preserves_existing_attempt_outputs(inputs46, existing):
    *_, evaluation, args, _ = inputs46
    assert command('prepare_v46.py', args).returncode == 0
    dest = evaluation/existing
    if dest.suffix:
        dest.write_text('preserve-me')
    else:
        dest.mkdir()
        dest = dest/'preserve.txt'
        dest.write_text('preserve-me')
    refused = command('run_v46.py', ['--evaluation', evaluation, '--code-root', ROOT, '--dry-run'])
    assert refused.returncode != 0 and 'Refuse overwriting' in refused.stderr
    assert dest.read_text() == 'preserve-me'


def test_v46_score_includes_v45_and_preserves_sources(inputs46):
    *_, evaluation, args, before = inputs46
    assert command('prepare_v46.py', args).returncode == 0
    link = {'artifact_id': 'synthetic-0', 'decision_element_id': 'synthetic-requirement', 'relation': 'supports'}
    simulate_completion(evaluation, [link, link])
    scored = command('score_v46.py', scoring_args(inputs46))
    assert scored.returncode == 0, scored.stderr
    m = json.loads((evaluation/'score'/'metrics.json').read_text())
    assert m['results']['all']['tp'] == 1 and m['results']['all']['predicted_exact_triples'] == 1
    assert m['comparison']['all']['api_v45_dev_f1'] == 0
    assert m['comparison']['all']['delta_v46_minus_v45'] == 1
    assert all(sha(path) == value for path, value in before.items())
    score_hash = sha(evaluation/'score'/'metrics.json')
    assert command('score_v46.py', scoring_args(inputs46)).returncode != 0
    assert sha(evaluation/'score'/'metrics.json') == score_hash


def test_v46_parent45_checkpoint_tamper_blocks_scoring(inputs46):
    *_, p45, evaluation, args, _ = inputs46
    assert command('prepare_v46.py', args).returncode == 0
    simulate_completion(evaluation)
    path = p45/'checkpoints/SIMULATED_V45_NO_PROVIDER.json'
    path.write_bytes(path.read_bytes()+b'\n ')
    result = command('score_v46.py', scoring_args(inputs46))
    assert result.returncode != 0 and 'Hash mismatch' in result.stderr
    assert not (evaluation/'score').exists()


def start_arguments(inputs):
    api, offline, frozen, p43, p44, p45, evaluation, *_ = inputs
    return ['start_v46_no_api.py', '--original-api', str(api), '--original-offline', str(offline),
            '--frozen', str(frozen), '--previous-v43', str(p43), '--previous-v44', str(p44),
            '--previous-v45', str(p45), '--evaluation', str(evaluation)]


def test_v46_start_three_local_steps_and_ready_pointer(inputs46, monkeypatch):
    evaluation = inputs46[6]
    module = load_tool('start_v46_no_api', monkeypatch)
    monkeypatch.setattr(module, 'READY_PATH', evaluation.parent/'fixture_V46_READY.json')
    from _score_core import code_tree_hash
    monkeypatch.setattr(module, 'EXPECTED_V46_CODE_SHA256', code_tree_hash(ROOT))
    calls = []
    monkeypatch.setattr(module.subprocess, 'run', lambda args, **kwargs: calls.append(args))
    monkeypatch.setattr(sys, 'argv', start_arguments(inputs46))
    module.main()
    assert len(calls) == 3 and calls[0][1:] == ['-m', 'pytest', '-q']
    assert Path(calls[1][1]).name == 'prepare_v46.py' and '--previous-v45' in calls[1]
    assert calls[2][-1] == '--dry-run' and not evaluation.exists()
    assert json.loads(module.READY_PATH.read_text())['evaluation'] == str(evaluation.resolve())


def test_v46_failed_preparation_preserves_ready_pointer(inputs46, monkeypatch):
    evaluation = inputs46[6]
    module = load_tool('start_v46_no_api', monkeypatch)
    ready = evaluation.parent/'fixture_V46_READY.json'
    write(ready, {'evaluation': 'preserve-previous'})
    before = sha(ready)
    monkeypatch.setattr(module, 'READY_PATH', ready)
    from _score_core import code_tree_hash
    monkeypatch.setattr(module, 'EXPECTED_V46_CODE_SHA256', code_tree_hash(ROOT))
    calls = []
    def fail(args, **kwargs):
        calls.append(args)
        if len(calls) == 2:
            raise subprocess.CalledProcessError(1, args)
    monkeypatch.setattr(module.subprocess, 'run', fail)
    monkeypatch.setattr(sys, 'argv', start_arguments(inputs46))
    with pytest.raises(subprocess.CalledProcessError):
        module.main()
    assert len(calls) == 2 and sha(ready) == before


def test_v46_bundle_integrity_and_exclusive_output(inputs46):
    *_, evaluation, args, _ = inputs46
    assert command('prepare_v46.py', args).returncode == 0
    simulate_completion(evaluation)
    out = evaluation.parent/'diagnostics46.zip'
    result = command('bundle_v46_diagnostics.py', ['--evaluation', evaluation, '--output', out])
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(out) as archive:
        manifest = json.loads(archive.read('DIAGNOSTIC_BUNDLE_MANIFEST.json'))
        import hashlib
        for name, expected in manifest['member_sha256'].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == expected
            assert archive.read(name) == (evaluation/name).read_bytes()
    before = sha(out)
    assert command('bundle_v46_diagnostics.py', ['--evaluation', evaluation, '--output', out]).returncode != 0
    assert sha(out) == before


@pytest.mark.parametrize('relative', ['run/report.json', 'inputs/'+DECISION,
                                     'checkpoints/SIMULATED_V46_NO_PROVIDER.json'])
def test_v46_bundle_tamper_never_creates_zip(inputs46, relative):
    *_, evaluation, args, _ = inputs46
    assert command('prepare_v46.py', args).returncode == 0
    simulate_completion(evaluation)
    path = evaluation/relative
    path.write_bytes(path.read_bytes()+b'\n ')
    out = evaluation.parent/'tampered46.zip'
    result = command('bundle_v46_diagnostics.py', ['--evaluation', evaluation, '--output', out])
    assert result.returncode != 0 and 'Hash mismatch' in result.stderr
    assert not out.exists()


def test_v46_start_uses_unused_localappdata_name(inputs46, monkeypatch, tmp_path):
    module = load_tool('start_v46_no_api', monkeypatch)
    local = tmp_path/'Windows LOCALAPPDATA'
    local.mkdir()
    (local/'ER1287Eval_v46Dev01').mkdir()
    monkeypatch.setenv('LOCALAPPDATA', str(local))
    monkeypatch.setattr(module, 'READY_PATH', local/'V46_READY.json')
    from _score_core import code_tree_hash
    monkeypatch.setattr(module, 'EXPECTED_V46_CODE_SHA256', code_tree_hash(ROOT))
    calls = []
    monkeypatch.setattr(module.subprocess, 'run', lambda args, **kwargs: calls.append(args))
    argv = start_arguments(inputs46)
    argv = argv[:argv.index('--evaluation')]
    monkeypatch.setattr(sys, 'argv', argv)
    module.main()
    assert calls[1][calls[1].index('--output')+1] == str(local/'ER1287Eval_v46Dev02')
    assert (local/'ER1287Eval_v46Dev01').is_dir()


@pytest.mark.parametrize('profile', ['event-delta', 'event-evidence'])
def test_v46_launcher_attests_actual_profile_without_provider(inputs46, monkeypatch, profile):
    *_, evaluation, args, _ = inputs46
    assert command('prepare_v46.py', args).returncode == 0
    module = load_tool('run_v46', monkeypatch)
    def fake_subprocess(invocation, **kwargs):
        assert invocation[invocation.index('--investigation-profile')+1] == 'event-evidence'
        simulate_completion(evaluation)
        (evaluation/'RUN_RECEIPT.json').unlink()
        path = evaluation/'run'/'manifest.json'
        manifest = json.loads(path.read_text())
        manifest['investigation_profile'] = profile
        write(path, manifest)
    monkeypatch.setattr(module.subprocess, 'run', fake_subprocess)
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-unused-no-provider')
    monkeypatch.setattr(sys, 'argv', ['run_v46.py', '--evaluation', str(evaluation), '--code-root', str(ROOT),
                                    '--i-approve-public-repository-excerpts-to-openai'])
    if profile == 'event-evidence':
        module.main()
        receipt = json.loads((evaluation/'RUN_RECEIPT.json').read_text())
        cfg = json.loads((evaluation/'DEV_PREP_MANIFEST.json').read_text())
        assert receipt['model'] == cfg['parent_v45_models']
        assert receipt['policy_change_note'] == cfg['policy_change_note']
        assert 'synthetic-unused' not in json.dumps(receipt)
    else:
        with pytest.raises(ValueError, match='run manifest provenance mismatch'):
            module.main()
        assert not (evaluation/'RUN_RECEIPT.json').exists()


def test_v46_prepared_model_mutation_blocks_even_dry_run(inputs46):
    *_, evaluation, args, _ = inputs46
    assert command('prepare_v46.py', args).returncode == 0
    path = evaluation/'DEV_PREP_MANIFEST.json'
    cfg = json.loads(path.read_text())
    cfg['models']['judge'] = 'unapproved-model-change'
    write(path, cfg)
    refused = command('run_v46.py', ['--evaluation', evaluation, '--code-root', ROOT, '--dry-run'])
    assert refused.returncode != 0 and 'preserve the pinned v4.5 model IDs' in refused.stderr
    assert not (evaluation/'RUN_ATTEMPT.json').exists()
