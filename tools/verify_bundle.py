#!/usr/bin/env python3
"""Verify this frozen export's bytes and recompute recorded results; no API."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

def verify_files(root):
    root = Path(root).resolve()
    data = json.loads((root/'ARTIFACT_MANIFEST.json').read_text(encoding='utf-8'))
    if data.get('artifact_kind') != 'EVORATIONALE_GITHUB_CODE_AND_DEVELOPMENT_EVIDENCE_EXPORT':
        raise ValueError('Unexpected artifact manifest')
    files = data['member_sha256']
    for name, expected in files.items():
        rel = PurePosixPath(name)
        if not rel.parts or rel.is_absolute() or any(p in ('.','..') or ':' in p for p in rel.parts):
            raise ValueError('Unsafe manifest path')
        member = root.joinpath(*rel.parts)
        if member.is_symlink() or not member.is_file() or root not in member.resolve().parents:
            raise ValueError('Missing/nonregular export member: '+name)
        if hashlib.sha256(member.read_bytes()).hexdigest() != expected:
            raise ValueError('Export member changed: '+name)
    return len(files)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    root = args.root.resolve()
    count = verify_files(root)
    subprocess.run([sys.executable, str(root/'tools/verify_data.py'), '--root', str(root)],
                   cwd=root, check=True)
    subprocess.run([sys.executable, str(root/'tools/verify_results.py'), '--root', str(root)],
                   cwd=root, check=True)
    print(json.dumps({'status':'GITHUB_EXPORT_BYTES_AND_RESULTS_VERIFIED_NO_API_CALLED',
                      'manifested_files':count,'provider_requests_made':0},indent=2))

if __name__ == '__main__':
    main()
