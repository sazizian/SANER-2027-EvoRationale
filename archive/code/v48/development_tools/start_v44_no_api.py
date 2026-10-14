#!/usr/bin/env python3
"""Run local tests, prepare a NEW v4.4 comparison, and dry-run without provider calls."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from _score_core import code_tree_hash
from prepare_v44 import COMPARISON_NOTE, EXPECTED_V44_CODE_SHA256, PROFILE


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
    parser.add_argument('--previous-v42', type=Path, help='Optional additional comparison; no automatic extra source')
    parser.add_argument('--evaluation', type=Path, help='Explicit NEW output; otherwise use unused LOCALAPPDATA name')
    args = parser.parse_args()
    # Resolve user paths before subprocesses switch cwd to the package root.
    # Otherwise a valid relative path is looked up under a different directory.
    for name in ('original_api', 'original_offline', 'frozen', 'previous_v43', 'previous_v42'):
        path = getattr(args, name)
        if path is not None:
            setattr(args, name, path.resolve())
    code = Path(__file__).resolve().parent.parent
    if code_tree_hash(code) != EXPECTED_V44_CODE_SHA256:
        raise ValueError('v4.4 Python source differs from the tested package')
    sources = {'--original-api': (args.original_api, 'RUN_RECEIPT.json'),
               '--original-offline': (args.original_offline, 'score/metrics.json'),
               '--frozen': (args.frozen, 'FREEZE_MANIFEST.json'),
               '--previous-v43': (args.previous_v43, 'score/metrics.json')}
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
        while (local/f'ER1287Eval_v44Dev{number:02d}').exists():
            number += 1
        evaluation = local/f'ER1287Eval_v44Dev{number:02d}'
    evaluation = evaluation.resolve()
    if evaluation.exists():
        raise FileExistsError(f'Refuse overwriting existing evaluation: {evaluation}')
    environment = os.environ.copy()
    environment['PYTHONUTF8'] = '1'
    def run(*arguments):
        subprocess.run([sys.executable, *map(str, arguments)], cwd=code, env=environment, check=True)
    print('v4.4 local tests and preparation only; no provider call will be made.', flush=True)
    run('-m', 'pytest', '-q')
    preparation = [code/'development_tools'/'prepare_v44.py', '--original-api', args.original_api,
                   '--original-offline', args.original_offline, '--frozen', args.frozen,
                   '--code-root', code, '--output', evaluation, '--previous-v43', args.previous_v43]
    if args.previous_v42 is not None:
        preparation.extend(['--previous-v42', args.previous_v42])
    run(*preparation)
    run(code/'development_tools'/'run_v44.py', '--evaluation', evaluation, '--code-root', code, '--dry-run')
    print(json.dumps({'status': 'V44_TESTS_AND_DRY_RUN_COMPLETED_NO_API_CALLED',
                      'code_root': str(code), 'evaluation': str(evaluation),
                      'investigation_profile': PROFILE, 'comparison_note': COMPARISON_NOTE}, indent=2))


if __name__ == '__main__':
    main()
