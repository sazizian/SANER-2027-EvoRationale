"""Closed-file atomic checkpoints with bounded Windows commit retries.

Only checkpoint publication is retried. The caller must stop if publication
fails; this module never retries inference or overwrites a pending snapshot.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile
from time import sleep as _sleep

_replace = os.replace
RETRY_DELAYS = (0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 2.0, 2.0)
WINDOWS_RETRY_CODES = frozenset({5, 32, 33})
CHECKPOINT_POLICY = 'CLOSED_UNIQUE_PENDING_ATOMIC_REPLACE_BOUNDED_WINDOWS_RETRIES_V1'


class CheckpointWriteError(RuntimeError):
    """A complete pending snapshot and prior checkpoint remain for inspection."""
    def __init__(self, checkpoint_path, pending_path, attempts, winerror):
        self.checkpoint_path = Path(checkpoint_path)
        self.pending_path = Path(pending_path)
        self.attempts = attempts
        self.winerror = winerror
        super().__init__(
            'checkpoint_publish_failed_after_bounded_retries; '
            f'WinError={winerror}; attempts={attempts}; '
            f'newest_snapshot_preserved={self.pending_path}; '
            'preserve this output and inspect before any new API run')


class CheckpointStore:
    """Single-writer run-local store, compatible with DecisionMemory JSON.

Successful replacement publishes the whole snapshot at once. Persistent
access denial leaves the previous destination untouched and retains the fully
written pending file. No delete-and-rewrite fallback is allowed. An unrelated
I/O error propagates immediately; a pending file may then be incomplete.
"""
    def __init__(self, directory):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, run_id):
        if not isinstance(run_id, str) or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', run_id) is None:
            raise ValueError('Unsafe checkpoint run ID')
        return self.dir / (run_id + '.json')

    def save(self, record):
        target = self._path(record.run_id)
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError('Checkpoint destination must be a regular file')
        # Serialize once before allocating the pending file. Each publication
        # retry uses these exact bytes and cannot regenerate a provider reply.
        raw = (json.dumps(record.asdict(), indent=2, sort_keys=True) + '\n').encode('utf-8')
        fd, name = tempfile.mkstemp(dir=self.dir, prefix=record.run_id + '-', suffix='.pending')
        pending = Path(name)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        # The writer is fully closed before every rename attempt on Windows.
        for attempt in range(len(RETRY_DELAYS) + 1):
            try:
                _replace(pending, target)
                return
            except OSError as exc:
                winerror = getattr(exc, 'winerror', None)
                if not isinstance(exc, PermissionError) or winerror not in WINDOWS_RETRY_CODES:
                    raise
                if attempt == len(RETRY_DELAYS):
                    raise CheckpointWriteError(target, pending, attempt + 1, winerror) from exc
                _sleep(RETRY_DELAYS[attempt])

    def get(self, run_id):
        from evorationale.memory import DecisionMemory
        path = self._path(run_id)
        return DecisionMemory(**json.loads(path.read_text(encoding='utf-8'))) if path.exists() else None
