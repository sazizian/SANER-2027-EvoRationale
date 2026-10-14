#!/usr/bin/env python3
"""Run local tests, prepare a NEW v4.7 comparison, and dry-run without provider calls."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from _score_core import code_tree_hash
from prepare_v47 import COMPARISON_NOTE, EXPECTED_V47_CODE_SHA256, MODEL_CHANGE_NOTE, POLICY_CHANGE_NOTE, NOMINATION_MODE, PROFILE

READY_PATH = Path(__file__).resolve().parent.parent/'V47_READY.json'


def preflight_ready_pointer(path: Path):
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError('V47_READY.json must be a regular convenience-pointer file')
    if path.exists() and not os.access(path, os.W_OK):
        raise PermissionError('V47_READY.json is not writable; no preparation was started')
    # Check the directory before tests/preparation, without touching an older
    # pointer or claiming an evaluation directory.
    with tempfile.NamedTemporaryFile(prefix='v47-ready-preflight-', dir=path.parent):
        pass


def save_ready_pointer(path: Path, data: dict):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', prefix='v47-ready-',
                                         dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    local = Path(os.environ['LOCALAPPDATA']) if os.environ.get('LOCALAPPDATA') else None
    def default(relative):
        return local/relative if local is not None else None
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-api', type=Path, default=default('ER1287Eval_API01'))
    parser.add_argument('--original-offline', type=Path, default=default('ER1287Eval_Offline01'))
    parser.add_argument('--frozen', type=Path,
                        default=default('ER1287Gold')/'KEP1287_Reviewer_Confirmed_Freeze' if local else None)
    parser.add_argument('--previous-v43', type=Path, default=default('ER1287Eval_v43Dev01'))
    parser.add_argument('--previous-v44', type=Path, default=default('ER1287Eval_v44Dev01'))
    parser.add_argument('--previous-v45', type=Path, default=default('ER1287Eval_v45Dev01'))
    parser.add_argument('--previous-v46', type=Path, default=default('ER1287Eval_v46Dev01'))
    parser.add_argument('--previous-v42', type=Path, help='Optional additional comparison; no automatic extra source')
    parser.add_argument('--evaluation', type=Path, help='Explicit NEW output; otherwise use unused LOCALAPPDATA name')
    args = parser.parse_args()
    # Resolve user paths before subprocesses switch cwd to the package root.
    # Otherwise a valid relative path is looked up under a different directory.
    for name in ('original_api', 'original_offline', 'frozen', 'previous_v43', 'previous_v44', 'previous_v45', 'previous_v46', 'previous_v42'):
        path = getattr(args, name)
        if path is not None:
            setattr(args, name, path.resolve())
    code = Path(__file__).resolve().parent.parent
    if code_tree_hash(code) != EXPECTED_V47_CODE_SHA256:
        raise ValueError('v4.7 Python source differs from the tested package')
    sources = {'--original-api': (args.original_api, 'RUN_RECEIPT.json'),
               '--original-offline': (args.original_offline, 'score/metrics.json'),
               '--frozen': (args.frozen, 'FREEZE_MANIFEST.json'),
               '--previous-v43': (args.previous_v43, 'score/metrics.json'),
               '--previous-v44': (args.previous_v44, 'score/metrics.json'),
               '--previous-v45': (args.previous_v45, 'score/metrics.json'),
               '--previous-v46': (args.previous_v46, 'score/metrics.json')}
    if args.previous_v42 is not None:
        sources['--previous-v42'] = (args.previous_v42, 'score/metrics.json')
    for flag, (folder, sentinel) in sources.items():
        if folder is None or not (folder/sentinel).is_file():
            raise FileNotFoundError(f'Supply {flag}: expected existing {sentinel} under {folder}')
    evaluation = args.evaluation
    if evaluation is None:
        if local is None:
            parser.error('--evaluation is required outside Windows LOCALAPPDATA')
        number = 1
        while (local/f'ER1287Eval_v47Dev{number:02d}').exists():
            number += 1
        evaluation = local/f'ER1287Eval_v47Dev{number:02d}'
    evaluation = evaluation.resolve()
    if evaluation.exists():
        raise FileExistsError(f'Refuse overwriting existing evaluation: {evaluation}')
    preflight_ready_pointer(READY_PATH)
    environment = os.environ.copy()
    environment['PYTHONUTF8'] = '1'
    def run(*arguments):
        subprocess.run([sys.executable, *map(str, arguments)], cwd=code, env=environment, check=True)
    print('v4.7 local tests and preparation only; no provider call will be made.', flush=True)
    run('-m', 'pytest', '-q')
    preparation = [code/'development_tools'/'prepare_v47.py', '--original-api', args.original_api,
                   '--original-offline', args.original_offline, '--frozen', args.frozen,
                   '--code-root', code, '--output', evaluation, '--previous-v43', args.previous_v43,
                   '--previous-v44', args.previous_v44, '--previous-v45', args.previous_v45,
                   '--previous-v46', args.previous_v46]
    if args.previous_v42 is not None:
        preparation.extend(['--previous-v42', args.previous_v42])
    run(*preparation)
    run(code/'development_tools'/'run_v47.py', '--evaluation', evaluation, '--code-root', code, '--dry-run')
    ready = {'status': 'V47_TESTS_AND_DRY_RUN_COMPLETED_NO_API_CALLED',
                      'code_root': str(code), 'evaluation': str(evaluation), 'python_executable': sys.executable,
                      'investigation_profile': PROFILE, 'comparison_note': COMPARISON_NOTE,
                      'nomination_mode': NOMINATION_MODE,
                      'model_change_note': MODEL_CHANGE_NOTE, 'policy_change_note': POLICY_CHANGE_NOTE}
    save_ready_pointer(READY_PATH, ready)
    print(json.dumps(ready, indent=2))


if __name__ == '__main__':
    main()
