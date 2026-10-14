#!/usr/bin/env python3
"""Offline release validation; tests the current local source tree, not live integrations."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parent.parent


def run(command):
    print('+', ' '.join(map(str,command)),flush=True)
    subprocess.run(command,cwd=ROOT,check=True)


def main():
    run([sys.executable,'-m','compileall','-q','evorationale','tests','scripts'])
    run([sys.executable,'-m','pytest','-q','tests'])
    with TemporaryDirectory() as temp:
        output=Path(temp)/'redis'
        run([sys.executable,'-m','evorationale','demo','--output',str(output)])
        report=json.loads((output/'report.json').read_text(encoding='utf-8'))
        trace=json.loads((output/'trace.json').read_text(encoding='utf-8'))
        manifest=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
        assert report['recommended_outcome']=='REOPEN',report
        assert report['verification']['status']=='PASS',report
        assert report['human_review_status']=='PENDING',report
        assert report['human_review_required'] is True,report
        assert 1<=len(trace)<=3, trace
        assert manifest['status']=='AWAITING_HUMAN_REVIEW',manifest
        assert (output/'checkpoints').is_dir()
    print('OFFLINE_RELEASE_SMOKE_TEST: PASS')


if __name__=='__main__':
    main()
