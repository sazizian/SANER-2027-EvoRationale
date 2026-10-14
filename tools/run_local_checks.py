#!/usr/bin/env python3
"""Run scoped source tests and both real-input forecasts with no hosted calls."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--skip-integrity', action='store_true',
                        help='Release construction only, before the final byte manifest exists')
    parser.add_argument('--skip-core-tests', action='store_true',
                        help='Use only when the unchanged core suite already passed in this export')
    args = parser.parse_args()
    root = args.root.resolve()
    environment = os.environ.copy()
    environment.pop('OPENAI_API_KEY', None)
    environment['PYTHONPATH'] = os.pathsep.join([str(root), environment.get('PYTHONPATH','')])
    def run(*command):
        subprocess.run([sys.executable,*map(str,command)], cwd=root, env=environment, check=True)
    if not args.skip_integrity:
        run(root/'tools/verify_bundle.py','--root',root)
    else:
        run(root/'tools/verify_data.py','--root',root)
        run(root/'tools/verify_results.py','--root',root)
    if not args.skip_core_tests:
        run('-m','pytest',root/'tests','-q')
    run('-m','pytest',root/'tools/tests','-q')
    with tempfile.TemporaryDirectory(prefix='evorationale-forecast-') as work:
        for name, script in [('primary_effects_windows_fix','start_primary_effect_no_api.py'),
                             ('scope_recheck','start_scope_recheck_no_api.py')]:
            target = Path(work)/name
            run(root/'experiments'/name/script,'--code-root',root,
                '--evaluation',root/'data/results/runs/v49','--output',target)
            if target.exists():
                raise ValueError('A no-API forecast unexpectedly created inference output')
    run(root/'tools/verify_results.py','--root',root)
    print(json.dumps({'status':'EXPORT_LOCAL_CHECKS_AND_FORECASTS_COMPLETED_NO_API_CALLED',
                      'provider_requests_made':0,'core_tests_run':not args.skip_core_tests,
                      'hosted_accuracy_measured_by_checks':False},indent=2))

if __name__ == '__main__':
    main()
