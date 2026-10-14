"""No-API v4.5 workflow checks using explicitly simulated completion receipts."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

from test_v44_development_tools import (
    DECISION, HISTORY, ROOT, command as prior_command, prepared_inputs, sha, write,
)

PARENT44_HASH = '9c7fc66afd6d315c5f02a7b4d88a10ca91c7ad43360fadba9d01cd3e71f91e3e'


def command(script, args):
    if script == 'prepare_v45.py':
        # The fixture does not substitute a production package pin on disk.
        wrapper = (f'import sys; sys.path.insert(0, {str(ROOT/"development_tools")!r}); '
                   'import prepare_v45; from _score_core import code_tree_hash; '
                   f'prepare_v45.EXPECTED_V45_CODE_SHA256 = code_tree_hash({str(ROOT)!r}); '
                   'prepare_v45.main()')
        arguments = [sys.executable, '-c', wrapper, *map(str, args)]
    else:
        arguments = [sys.executable, str(ROOT/'development_tools'/script), *map(str, args)]
    return subprocess.run(arguments, cwd=ROOT, capture_output=True, text=True)


@pytest.fixture
def prepared_v45_inputs(prepared_inputs):
    api, offline, frozen, parent43, parent44, args44, _ = prepared_inputs
    prepared = prior_command('prepare_v44.py', args44)
    assert prepared.returncode == 0, prepared.stderr
    config = json.loads((parent44/'DEV_PREP_MANIFEST.json').read_text())
    # Explicitly simulated parent source attestation; no hosted run is performed.
    config['v44_python_sha256'] = PARENT44_HASH
    write(parent44/'DEV_PREP_MANIFEST.json', config)
    write(parent44/'run'/'report.json', {'verified_evidence': [], 'verification': {'status': 'UNRESOLVED'}})
    write(parent44/'run'/'manifest.json', {
        'run_id': 'SIMULATED_PARENT44_NO_PROVIDER', 'mode': 'api', 'investigation_profile': 'event-complete',
        'decision_sha256': config['runtime_s0_sha256'], 'history_sha256': config['history_sha256'],
        'report_sha256': sha(parent44/'run'/'report.json'),
    })
    write(parent44/'RUN_RECEIPT.json', {
        'run_id': 'SIMULATED_PARENT44_NO_PROVIDER', 'mode': 'api', 'investigation_profile': 'event-complete',
        'status': 'V44_DEV_HOSTED_RUN_COMPLETED_AND_HASHED', 'code_tree_sha256': PARENT44_HASH,
        'model': config['models'], 'nominal_budgets': config['budgets'],
        'prep_sha256': sha(parent44/'DEV_PREP_MANIFEST.json'),
        'run_manifest_sha256': sha(parent44/'run'/'manifest.json'),
        'run_report_sha256': sha(parent44/'run'/'report.json'),
    })
    metrics = json.loads((parent43/'score'/'metrics.json').read_text())
    metrics['v44_run_report_sha256'] = sha(parent44/'run'/'report.json')
    write(parent44/'score'/'metrics.json', metrics)
    evaluation = parent44.parent/'evaluation45'
    args = list(args44)
    args[args.index('--output')+1] = evaluation
    args.extend(['--previous-v44', parent44])
    before = {path: sha(path) for folder in (api, offline, frozen, parent43, parent44)
              for path in folder.rglob('*') if path.is_file()}
    return api, offline, frozen, parent43, parent44, evaluation, args, before


def simulate_v45_completion(evaluation, evidence=None):
    from evorationale.model import validate_state
    config = json.loads((evaluation/'DEV_PREP_MANIFEST.json').read_text())
    write(evaluation/'run'/'report.json', {
        'verified_evidence': evidence or [], 'verification': {'status': 'UNRESOLVED'},
    })
    write(evaluation/'run'/'manifest.json', {
        'run_id': 'SIMULATED_V45_NO_PROVIDER', 'mode': 'api', 'investigation_profile': 'event-delta',
        'nomination_mode': config['nomination_mode'],
        'decision_sha256': config['runtime_s0_sha256'], 'history_sha256': config['history_sha256'],
        'report_sha256': sha(evaluation/'run'/'report.json'),
    })
    checkpoint_relative = 'checkpoints/SIMULATED_V45_NO_PROVIDER.json'
    write(evaluation/checkpoint_relative, {
        'run_id': 'SIMULATED_V45_NO_PROVIDER', 'report': json.loads((evaluation/'run'/'report.json').read_text()),
        'initial_state': validate_state(json.loads((evaluation/'inputs'/DECISION).read_text())),
    })
    write(evaluation/'RUN_RECEIPT.json', {
        'run_id': 'SIMULATED_V45_NO_PROVIDER', 'mode': 'api', 'investigation_profile': 'event-delta',
        'nomination_mode': config['nomination_mode'],
        'status': 'V45_DEV_HOSTED_RUN_COMPLETED_AND_HASHED', 'code_tree_sha256': config['v45_python_sha256'],
        'model': config['models'], 'parent_v44_models': config['parent_v44_models'],
        'nominal_budgets': config['budgets'], 'prep_sha256': sha(evaluation/'DEV_PREP_MANIFEST.json'),
        'run_manifest_sha256': sha(evaluation/'run'/'manifest.json'),
        'run_report_sha256': sha(evaluation/'run'/'report.json'),
        'checkpoint_relative_path': checkpoint_relative, 'checkpoint_sha256': sha(evaluation/checkpoint_relative),
    })


def scoring_args(inputs):
    api, offline, frozen, parent43, parent44, evaluation, *_ = inputs
    return ['--evaluation', evaluation, '--frozen', frozen, '--code-root', ROOT,
            '--original-api', api, '--original-offline', offline,
            '--previous-v43', parent43, '--previous-v44', parent44]


def load_tool(name, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'development_tools'))
    spec = importlib.util.spec_from_file_location('test45_' + name, ROOT/'development_tools'/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v45_reuses_exact_inputs_and_budgets_and_explicitly_changes_judge(prepared_v45_inputs):
    *_, evaluation, args, before = prepared_v45_inputs
    prepared = command('prepare_v45.py', args)
    assert prepared.returncode == 0, prepared.stderr
    config = json.loads((evaluation/'DEV_PREP_MANIFEST.json').read_text())
    assert config['models'] == {'linker': 'fixture-reused-linker', 'judge': 'fixture-reused-linker'}
    assert config['parent_v44_models']['judge'] == 'fixture-reused-judge'
    assert config['budgets'] == {'max_rounds': 6, 'max_queries': 12, 'max_reads': 36, 'max_input_tokens': 100000}
    assert config['previous_v44']['code_tree_sha256'] == PARENT44_HASH
    assert config['nomination_mode'] == 'none'
    assert config['gold_labels_in_agent_inputs'] is False
    assert 'not an equal-model or equal-compute comparison' in config['model_change_note']
    assert sorted(p.name for p in (evaluation/'inputs').iterdir()) == sorted([DECISION, HISTORY])
    assert 'PRIVATE_GOLD_MARKER' not in ''.join(p.read_text() for p in evaluation.rglob('*') if p.is_file())
    dry = command('run_v45.py', ['--evaluation', evaluation, '--code-root', ROOT, '--dry-run'])
    assert dry.returncode == 0, dry.stderr
    result = json.loads(dry.stdout)
    invocation = result['command']
    assert invocation[invocation.index('--investigation-profile')+1] == 'event-delta'
    assert invocation[invocation.index('--judge-model')+1] == config['models']['linker']
    assert invocation[invocation.index('--delta-nomination')+1] == 'none'
    assert result['model_change_note'] == config['model_change_note']
    assert not (evaluation/'run').exists() and not (evaluation/'RUN_ATTEMPT.json').exists()
    assert all(sha(path) == value for path, value in before.items())


@pytest.mark.parametrize('relative', ['DEV_PREP_MANIFEST.json', 'run/manifest.json', 'run/report.json', 'inputs/'+HISTORY])
def test_v45_parent_tamper_rejected_before_any_new_preparation(prepared_v45_inputs, relative):
    *_, parent44, evaluation, args, _ = prepared_v45_inputs
    file = parent44/relative
    file.write_bytes(file.read_bytes()+b'\n ')
    refused = command('prepare_v45.py', args)
    assert refused.returncode != 0 and 'Hash mismatch' in refused.stderr
    assert not evaluation.exists()


@pytest.mark.parametrize('existing', ['run', 'checkpoints', 'score', 'RUN_RECEIPT.json', 'RUN_ATTEMPT.json'])
def test_v45_fresh_attempt_guard_preserves_all_existing_outputs(prepared_v45_inputs, existing):
    *_, evaluation, args, _ = prepared_v45_inputs
    assert command('prepare_v45.py', args).returncode == 0
    destination = evaluation/existing
    if destination.suffix:
        destination.write_text('preserve-me')
    else:
        destination.mkdir()
        destination = destination/'preserve.txt'
        destination.write_text('preserve-me')
    refused = command('run_v45.py', ['--evaluation', evaluation, '--code-root', ROOT, '--dry-run'])
    assert refused.returncode != 0 and 'Refuse overwriting' in refused.stderr
    assert destination.read_text() == 'preserve-me'


def test_v45_exact_triple_score_has_v44_and_v43_comparisons_and_preserves_sources(prepared_v45_inputs):
    *_, evaluation, args, before = prepared_v45_inputs
    assert command('prepare_v45.py', args).returncode == 0
    link = {'artifact_id': 'synthetic-0', 'decision_element_id': 'synthetic-requirement', 'relation': 'supports'}
    simulate_v45_completion(evaluation, [link, link])
    scored = command('score_v45.py', scoring_args(prepared_v45_inputs))
    assert scored.returncode == 0, scored.stderr
    metrics = json.loads((evaluation/'score'/'metrics.json').read_text())
    assert metrics['results']['all']['tp'] == 1
    assert metrics['results']['all']['predicted_exact_triples'] == 1
    assert metrics['comparison']['all']['api_v44_dev_f1'] == 0.0
    assert metrics['comparison']['all']['delta_v45_minus_v44'] == 1.0
    assert metrics['comparison']['all']['delta_v45_minus_v43'] == 1.0
    assert all(sha(path) == value for path, value in before.items())
    score_hash = sha(evaluation/'score'/'metrics.json')
    refused = command('score_v45.py', scoring_args(prepared_v45_inputs))
    assert refused.returncode != 0 and 'overwrite' in refused.stderr
    assert sha(evaluation/'score'/'metrics.json') == score_hash


@pytest.mark.parametrize('relative', ['RUN_RECEIPT.json', 'run/report.json', 'score/metrics.json', 'inputs/'+DECISION])
def test_v45_old_comparator_tamper_blocks_scoring_before_label_interpretation(prepared_v45_inputs, relative):
    *_, parent44, evaluation, args, _ = prepared_v45_inputs
    assert command('prepare_v45.py', args).returncode == 0
    simulate_v45_completion(evaluation)
    file = parent44/relative
    file.write_bytes(file.read_bytes()+b'\n ')
    refused = command('score_v45.py', scoring_args(prepared_v45_inputs))
    assert refused.returncode != 0 and 'Hash mismatch' in refused.stderr
    assert not (evaluation/'score').exists()


def test_v45_start_only_tests_prepares_and_dry_runs(prepared_v45_inputs, monkeypatch, capsys):
    api, offline, frozen, parent43, parent44, evaluation, *_ = prepared_v45_inputs
    module = load_tool('start_v45_no_api', monkeypatch)
    monkeypatch.setattr(module, 'READY_PATH', evaluation.parent/'fixture_V45_READY.json')
    from _score_core import code_tree_hash
    monkeypatch.setattr(module, 'EXPECTED_V45_CODE_SHA256', code_tree_hash(ROOT))
    calls = []
    monkeypatch.setattr(module.subprocess, 'run', lambda arguments, **kwargs: calls.append(arguments))
    monkeypatch.setattr(sys, 'argv', ['start_v45_no_api.py', '--original-api', str(api), '--original-offline', str(offline),
                                    '--frozen', str(frozen), '--previous-v43', str(parent43), '--previous-v44', str(parent44),
                                    '--evaluation', str(evaluation)])
    module.main()
    assert len(calls) == 3 and calls[0][1:] == ['-m', 'pytest', '-q']
    assert Path(calls[1][1]).name == 'prepare_v45.py'
    assert '--previous-v44' in calls[1]
    assert calls[2][-1] == '--dry-run'
    assert not evaluation.exists()
    ready = json.loads(module.READY_PATH.read_text())
    assert ready['evaluation'] == str(evaluation.resolve())
    assert ready['python_executable'] == sys.executable
    assert 'V45_TESTS_AND_DRY_RUN_COMPLETED_NO_API_CALLED' in capsys.readouterr().out


def test_v45_relative_windows_paths_with_spaces_and_unicode(prepared_v45_inputs, monkeypatch, tmp_path):
    api, offline, frozen, parent43, parent44, *_ = prepared_v45_inputs
    caller = tmp_path/'caller folder caf\u00e9'
    caller.mkdir()
    folders = {}
    for flag, source in [('--original-api', api), ('--original-offline', offline), ('--frozen', frozen),
                         ('--previous-v43', parent43), ('--previous-v44', parent44)]:
        destination = caller/(source.name+' r\u00e9sum\u00e9')
        shutil.copytree(source, destination)
        folders[flag] = destination
    evaluation = caller/'new evaluation na\u00efve'
    module = load_tool('start_v45_no_api', monkeypatch)
    monkeypatch.setattr(module, 'READY_PATH', evaluation.parent/'fixture_V45_READY.json')
    from _score_core import code_tree_hash
    monkeypatch.setattr(module, 'EXPECTED_V45_CODE_SHA256', code_tree_hash(ROOT))
    actual_run = subprocess.run
    calls = []
    def local_subprocess(arguments, **kwargs):
        calls.append(arguments)
        if arguments[1:4] == ['-m', 'pytest', '-q']:
            return subprocess.CompletedProcess(arguments, 0)
        if Path(arguments[1]).name == 'prepare_v45.py':
            wrapper = (f'import sys; sys.path.insert(0, {str(ROOT/"development_tools")!r}); '
                       'import prepare_v45; from _score_core import code_tree_hash; '
                       f'prepare_v45.EXPECTED_V45_CODE_SHA256 = code_tree_hash({str(ROOT)!r}); '
                       'prepare_v45.main()')
            arguments = [arguments[0], '-c', wrapper, *arguments[2:]]
        result = actual_run(arguments, **kwargs, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        return result
    monkeypatch.setattr(module.subprocess, 'run', local_subprocess)
    argv = ['start_v45_no_api.py']
    for flag, source in folders.items():
        argv.extend([flag, source.name])
    argv.extend(['--evaluation', evaluation.name])
    monkeypatch.chdir(caller)
    monkeypatch.setattr(sys, 'argv', argv)
    module.main()
    assert len(calls) == 3
    for flag, folder in folders.items():
        assert calls[1][calls[1].index(flag)+1] == str(folder.resolve())
    assert (evaluation/'DEV_PREP_MANIFEST.json').is_file()
    assert not (evaluation/'RUN_ATTEMPT.json').exists()
    assert not (evaluation/'run').exists()
    assert json.loads(module.READY_PATH.read_text())['evaluation'] == str(evaluation.resolve())


def test_v45_start_allocates_unused_localappdata_evaluation(prepared_v45_inputs, monkeypatch, tmp_path):
    api, offline, frozen, parent43, parent44, *_ = prepared_v45_inputs
    local = tmp_path/'synthetic Windows LOCALAPPDATA'
    local.mkdir()
    (local/'ER1287Eval_v45Dev01').mkdir()
    module = load_tool('start_v45_no_api', monkeypatch)
    monkeypatch.setattr(module, 'READY_PATH', local/'V45_READY.json')
    from _score_core import code_tree_hash
    monkeypatch.setattr(module, 'EXPECTED_V45_CODE_SHA256', code_tree_hash(ROOT))
    monkeypatch.setenv('LOCALAPPDATA', str(local))
    calls = []
    monkeypatch.setattr(module.subprocess, 'run', lambda arguments, **kwargs: calls.append(arguments))
    monkeypatch.setattr(sys, 'argv', ['start_v45_no_api.py', '--original-api', str(api), '--original-offline', str(offline),
                                    '--frozen', str(frozen), '--previous-v43', str(parent43), '--previous-v44', str(parent44)])
    module.main()
    assert calls[1][calls[1].index('--output')+1] == str(local/'ER1287Eval_v45Dev02')
    assert (local/'ER1287Eval_v45Dev01').is_dir()


@pytest.mark.parametrize('profile', ['event-complete', 'event-delta'])
def test_v45_completion_receipt_requires_actual_profile_without_provider(prepared_v45_inputs, monkeypatch, profile):
    *_, evaluation, args, _ = prepared_v45_inputs
    assert command('prepare_v45.py', args).returncode == 0
    module = load_tool('run_v45', monkeypatch)
    def local_only_subprocess(arguments, **kwargs):
        assert arguments[arguments.index('--investigation-profile')+1] == 'event-delta'
        simulate_v45_completion(evaluation)
        # The launcher creates the real completion receipt after this fixture.
        (evaluation/'RUN_RECEIPT.json').unlink()
        manifest_path = evaluation/'run'/'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['investigation_profile'] = profile
        write(manifest_path, manifest)
    monkeypatch.setattr(module.subprocess, 'run', local_only_subprocess)
    monkeypatch.setenv('OPENAI_API_KEY', 'unused-synthetic-no-provider')
    monkeypatch.setattr(sys, 'argv', ['run_v45.py', '--evaluation', str(evaluation), '--code-root', str(ROOT),
                                    '--i-approve-public-repository-excerpts-to-openai'])
    if profile == 'event-delta':
        module.main()
        receipt = json.loads((evaluation/'RUN_RECEIPT.json').read_text())
        assert receipt['parent_v44_models']['judge'] == 'fixture-reused-judge'
        assert receipt['model']['judge'] == 'fixture-reused-linker'
        assert 'unused-synthetic' not in json.dumps(receipt)
    else:
        with pytest.raises(ValueError, match='run manifest provenance mismatch'):
            module.main()
        assert not (evaluation/'RUN_RECEIPT.json').exists()


def test_v45_ready_pointer_updates_only_after_complete_success(prepared_v45_inputs, monkeypatch):
    api, offline, frozen, parent43, parent44, evaluation, *_ = prepared_v45_inputs
    module = load_tool('start_v45_no_api', monkeypatch)
    ready_path = evaluation.parent/'fixture_V45_READY.json'
    write(ready_path, {'evaluation': 'preserve-previous-ready-run'})
    previous_hash = sha(ready_path)
    monkeypatch.setattr(module, 'READY_PATH', ready_path)
    from _score_core import code_tree_hash
    monkeypatch.setattr(module, 'EXPECTED_V45_CODE_SHA256', code_tree_hash(ROOT))
    calls = []
    def fail_preparation(arguments, **kwargs):
        calls.append(arguments)
        if len(calls) == 2:
            raise subprocess.CalledProcessError(1, arguments)
    monkeypatch.setattr(module.subprocess, 'run', fail_preparation)
    monkeypatch.setattr(sys, 'argv', ['start_v45_no_api.py', '--original-api', str(api), '--original-offline', str(offline),
                                    '--frozen', str(frozen), '--previous-v43', str(parent43), '--previous-v44', str(parent44),
                                    '--evaluation', str(evaluation)])
    with pytest.raises(subprocess.CalledProcessError):
        module.main()
    assert len(calls) == 2 and sha(ready_path) == previous_hash


def test_v45_unwritable_ready_pointer_fails_before_tests_or_preparation(prepared_v45_inputs, monkeypatch):
    api, offline, frozen, parent43, parent44, evaluation, *_ = prepared_v45_inputs
    module = load_tool('start_v45_no_api', monkeypatch)
    ready_path = evaluation.parent/'fixture_V45_READY.json'
    write(ready_path, {'evaluation': 'preserve-previous-ready-run'})
    previous_hash = sha(ready_path)
    monkeypatch.setattr(module, 'READY_PATH', ready_path)
    from _score_core import code_tree_hash
    monkeypatch.setattr(module, 'EXPECTED_V45_CODE_SHA256', code_tree_hash(ROOT))
    monkeypatch.setattr(module.os, 'access', lambda *args: False)
    calls = []
    monkeypatch.setattr(module.subprocess, 'run', lambda arguments, **kwargs: calls.append(arguments))
    monkeypatch.setattr(sys, 'argv', ['start_v45_no_api.py', '--original-api', str(api), '--original-offline', str(offline),
                                    '--frozen', str(frozen), '--previous-v43', str(parent43), '--previous-v44', str(parent44),
                                    '--evaluation', str(evaluation)])
    with pytest.raises(PermissionError, match='no preparation was started'):
        module.main()
    assert not calls and sha(ready_path) == previous_hash and not evaluation.exists()


def test_v45_bundle_verifies_checkpoint_and_preserves_relative_names(prepared_v45_inputs):
    *_, evaluation, args, _ = prepared_v45_inputs
    assert command('prepare_v45.py', args).returncode == 0
    simulate_v45_completion(evaluation)
    scored = command('score_v45.py', scoring_args(prepared_v45_inputs))
    assert scored.returncode == 0, scored.stderr
    output = evaluation.parent/'diagnostics45.zip'
    bundled = command('bundle_v45_diagnostics.py', ['--evaluation', evaluation, '--output', output])
    assert bundled.returncode == 0, bundled.stderr
    assert json.loads(bundled.stdout)['status'] == 'V45_DIAGNOSTICS_VERIFIED_NO_API_CALLED'
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert {'DEV_PREP_MANIFEST.json', 'RUN_RECEIPT.json', 'run/manifest.json', 'run/report.json',
                'inputs/'+DECISION, 'inputs/'+HISTORY, 'checkpoints/SIMULATED_V45_NO_PROVIDER.json',
                'score/metrics.json', 'score/link_errors.csv', 'DIAGNOSTIC_BUNDLE_MANIFEST.json'} == names
        manifest = json.loads(archive.read('DIAGNOSTIC_BUNDLE_MANIFEST.json'))
        import hashlib
        for name, expected in manifest['member_sha256'].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == expected
            assert archive.read(name) == (evaluation/name).read_bytes()
    before = sha(output)
    refused = command('bundle_v45_diagnostics.py', ['--evaluation', evaluation, '--output', output])
    assert refused.returncode != 0 and 'overwriting' in refused.stderr
    assert sha(output) == before


@pytest.mark.parametrize('relative', ['DEV_PREP_MANIFEST.json', 'run/manifest.json', 'run/report.json',
                                     'inputs/'+DECISION, 'inputs/'+HISTORY, 'checkpoints/SIMULATED_V45_NO_PROVIDER.json'])
def test_v45_bundle_tamper_rejected_before_zip_creation(prepared_v45_inputs, relative):
    *_, evaluation, args, _ = prepared_v45_inputs
    assert command('prepare_v45.py', args).returncode == 0
    simulate_v45_completion(evaluation)
    file = evaluation/relative
    file.write_bytes(file.read_bytes()+b'\n ')
    output = evaluation.parent/'tampered45.zip'
    refused = command('bundle_v45_diagnostics.py', ['--evaluation', evaluation, '--output', output])
    assert refused.returncode != 0 and 'Hash mismatch' in refused.stderr
    assert not output.exists()


def test_v45_bundle_missing_checkpoint_is_clear_and_never_creates_zip(prepared_v45_inputs):
    *_, evaluation, args, _ = prepared_v45_inputs
    assert command('prepare_v45.py', args).returncode == 0
    simulate_v45_completion(evaluation)
    (evaluation/'checkpoints'/'SIMULATED_V45_NO_PROVIDER.json').unlink()
    output = evaluation.parent/'missing45.zip'
    refused = command('bundle_v45_diagnostics.py', ['--evaluation', evaluation, '--output', output])
    assert refused.returncode != 0 and 'Missing or nonregular diagnostic file' in refused.stderr
    assert not output.exists()


def test_v45_bundle_blocks_path_traversal_in_checkpoint_id(prepared_v45_inputs):
    *_, evaluation, args, _ = prepared_v45_inputs
    assert command('prepare_v45.py', args).returncode == 0
    simulate_v45_completion(evaluation)
    manifest_path, receipt_path = evaluation/'run'/'manifest.json', evaluation/'RUN_RECEIPT.json'
    manifest, receipt = json.loads(manifest_path.read_text()), json.loads(receipt_path.read_text())
    manifest['run_id'] = receipt['run_id'] = '../escape'
    write(manifest_path, manifest)
    receipt['run_manifest_sha256'] = sha(manifest_path)
    write(receipt_path, receipt)
    output = evaluation.parent/'unsafe45.zip'
    refused = command('bundle_v45_diagnostics.py', ['--evaluation', evaluation, '--output', output])
    assert refused.returncode != 0 and 'Unsafe checkpoint run ID' in refused.stderr
    assert not output.exists()


def test_v45_normalized_checkpoint_state_retains_attested_raw_input_bytes(prepared_v45_inputs, monkeypatch):
    *_, evaluation, args, _ = prepared_v45_inputs
    assert command('prepare_v45.py', args).returncode == 0
    from datetime import timedelta, timezone
    from evorationale.model import ELEMENT_FIELDS, parse_timestamp, validate_state
    raw = json.loads((evaluation/'inputs'/DECISION).read_text())
    for field in ('accepted_at', 'cutoff_at'):
        raw[field] = parse_timestamp(raw[field]).astimezone(timezone(timedelta(hours=-5))).isoformat()
    # Omit one legal empty optional collection, while retaining every central
    # rationale ID and the other original decision elements.
    central = set(raw['central_element_ids'])
    empty_field = next(field for field in ELEMENT_FIELDS
                       if not any(item['id'] in central for item in raw.get(field, [])))
    raw[empty_field] = []
    omitted = [field for field in ELEMENT_FIELDS if not raw.get(field)]
    assert omitted
    for field in omitted:
        raw.pop(field, None)
    state_path = evaluation/'inputs'/DECISION
    write(state_path, raw)
    config_path = evaluation/'DEV_PREP_MANIFEST.json'
    config = json.loads(config_path.read_text())
    config['runtime_s0_sha256'] = sha(state_path)
    write(config_path, config)
    raw_sha256 = sha(state_path)
    assert validate_state(raw) != raw
    module = load_tool('run_v45', monkeypatch)
    def normalized_local_subprocess(arguments, **kwargs):
        simulate_v45_completion(evaluation)
        (evaluation/'RUN_RECEIPT.json').unlink()
    monkeypatch.setattr(module.subprocess, 'run', normalized_local_subprocess)
    monkeypatch.setenv('OPENAI_API_KEY', 'unused-synthetic-no-provider')
    monkeypatch.setattr(sys, 'argv', ['run_v45.py', '--evaluation', str(evaluation), '--code-root', str(ROOT),
                                    '--i-approve-public-repository-excerpts-to-openai'])
    module.main()
    bundle_module = load_tool('bundle_v45_diagnostics', monkeypatch)
    members, _, _ = bundle_module.verified_members(evaluation)
    assert members['inputs/'+DECISION] == state_path.read_bytes()
    assert sha(state_path) == raw_sha256
