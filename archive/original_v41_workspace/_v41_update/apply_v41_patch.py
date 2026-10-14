"""Offline, validated v4 -> v4.1 patch installer. Never touches user data or secrets."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,default=Path.cwd())
    args=p.parse_args()
    source=Path(__file__).resolve().parent
    target=args.project.resolve()
    if not (target/'pyproject.toml').is_file() or not (target/'evorationale'/'__init__.py').is_file():
        raise SystemExit('ERROR: Please run from the EvoRationale v4 project root containing pyproject.toml.')
    project_config=(target/'pyproject.toml').read_text(encoding='utf-8')
    if 'version = "4.0.0rc1"' not in project_config and 'version = "4.1.0rc1"' not in project_config:
        raise SystemExit('ERROR: This patch is intended only for EvoRationale 4.0.0rc1 / 4.1.0rc1.')
    manifest=json.loads((source/'PATCH_SHA256.json').read_text(encoding='utf-8'))
    for relative,expected in manifest.items():
        path=source/relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise SystemExit(f'ERROR: Patch hash mismatch or missing file: {relative}')
        if '..' in Path(relative).parts or Path(relative).is_absolute():
            raise SystemExit('ERROR: Invalid patch destination path')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=target/f'backup_before_v41_{stamp}'
    if backup.exists():
        raise SystemExit('ERROR: backup name collision; retry in a minute')
    # Backup all overwrite targets BEFORE overwriting any of them.
    backup.mkdir()
    try:
        for relative in manifest:
            destination=target/relative
            if destination.exists():
                snapshot=backup/relative
                snapshot.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(destination,snapshot)
        for relative in manifest:
            destination=target/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source/relative,destination)
    except Exception as exc:
        # Best-effort rollback for files that existed before the installation.
        for relative in manifest:
            before=backup/relative
            if before.is_file():
                (target/relative).parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(before,target/relative)
            else:
                created=target/relative
                if created.exists():
                    created.unlink()
        raise SystemExit(f'ERROR: Patch installation failed and rollback attempted: {exc}') from exc
    print(json.dumps({'status':'V41_PATCH_APPLIED',
                      'backups_at':str(backup),'project_root':str(target),
                      'patched_files':len(manifest),
                      'note':'GitHub history, decisions, outputs, venv and API keys were not changed.'},
                     indent=2))


if __name__=='__main__':
    main()
