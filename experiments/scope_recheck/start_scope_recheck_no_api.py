#!/usr/bin/env python3
"""Run portable local tests and forecast cached checks; never call a provider."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

from _kit_common import load_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code-root', required=True, type=Path)
    parser.add_argument('--evaluation', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = load_code(args.code_root)
    kit = Path(__file__).resolve().parent
    environment = os.environ.copy()
    environment['PYTHONPATH'] = os.pathsep.join([str(root), str(kit), environment.get('PYTHONPATH', '')])
    print('Local tests and cached-check forecast only; no API will be called.', flush=True)
    subprocess.run([sys.executable, '-m', 'pytest', str(kit/'test_scope_checker.py'),
                    str(kit/'test_scope_workflows.py'), '-q'], env=environment, cwd=kit, check=True)
    subprocess.run([sys.executable, str(kit/'run_scope_recheck.py'), '--code-root', str(root),
                    '--evaluation', str(args.evaluation.resolve()), '--output', str(args.output.resolve()),
                    '--mode', 'dry-run'], env=environment, cwd=kit, check=True)


if __name__ == '__main__':
    main()
