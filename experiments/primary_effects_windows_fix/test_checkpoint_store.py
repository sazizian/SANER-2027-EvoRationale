"""Checkpoint commit fault tests; no model, credential or hosted transport.

Fault injection runs on every platform. The final native Windows test exercises
an actual file handle that denies deletion while a bounded retry is underway.
"""
import ctypes
import errno
import json
from pathlib import Path
import sys
import threading

import pytest

import checkpoint_store as checkpoints
from evorationale.memory import DecisionMemory


def _record(token_count=1):
    return DecisionMemory(run_id="checkpoint-test", initial_state={"fixed": "unchanged"},
        status="RUNNING", token_count=token_count)


def _windows_error(code=5):
    error = PermissionError(errno.EACCES, "Injected Windows checkpoint denial")
    error.winerror = code
    return error


@pytest.mark.parametrize("code", [5, 32, 33])
def test_transient_windows_commit_retries_identical_closed_pending_once(monkeypatch, tmp_path, code):
    store = checkpoints.CheckpointStore(tmp_path)
    record = _record(17)
    original_fdopen = checkpoints.os.fdopen
    original_replace = checkpoints._replace
    streams, commits, sleeps, serializations = [], [], [], []
    original_asdict = record.asdict

    def serialize():
        serializations.append(True)
        return original_asdict()

    def fdopen(*args, **kwargs):
        stream = original_fdopen(*args, **kwargs)
        streams.append(stream)
        return stream

    def commit(pending, target):
        assert all(stream.closed for stream in streams)
        commits.append((Path(pending), Path(target), Path(pending).read_bytes()))
        if len(commits) <= 2:
            raise _windows_error(code)
        return original_replace(pending, target)

    monkeypatch.setattr(record, "asdict", serialize)
    monkeypatch.setattr(checkpoints.os, "fdopen", fdopen)
    monkeypatch.setattr(checkpoints, "_replace", commit)
    monkeypatch.setattr(checkpoints, "_sleep", sleeps.append)
    store.save(record)
    assert len(serializations) == len(streams) == 1
    assert len(commits) == 3
    assert len({path for path, _, _ in commits}) == 1
    assert len({raw for _, _, raw in commits}) == 1
    assert sleeps == list(checkpoints.RETRY_DELAYS[:2])
    assert store.get(record.run_id).asdict() == record.asdict()
    assert not list(tmp_path.glob("*.pending"))


@pytest.mark.parametrize("code", [5, 32, 33])
def test_exhausted_windows_commit_preserves_old_bytes_and_latest_pending(monkeypatch, tmp_path, code):
    store = checkpoints.CheckpointStore(tmp_path)
    old = _record(1)
    store.save(old)
    target = tmp_path / (old.run_id + ".json")
    prior = target.read_bytes()
    latest = _record(108)
    latest.trace = [{"focused_chunks": [{"status": "VALIDATED", "response": "retained"}]}]
    attempts, sleeps = [], []

    def denied(pending, destination):
        attempts.append((Path(pending), Path(destination), Path(pending).read_bytes()))
        assert target.read_bytes() == prior
        raise _windows_error(code)

    monkeypatch.setattr(checkpoints, "_replace", denied)
    monkeypatch.setattr(checkpoints, "_sleep", sleeps.append)
    with pytest.raises(checkpoints.CheckpointWriteError) as failure:
        store.save(latest)
    error = failure.value
    assert error.attempts == len(attempts) == len(checkpoints.RETRY_DELAYS) + 1
    assert error.winerror == code
    assert error.checkpoint_path == target
    assert target.read_bytes() == prior
    assert json.loads(error.pending_path.read_bytes()) == latest.asdict()
    assert error.pending_path.parent == target.parent
    assert sleeps == list(checkpoints.RETRY_DELAYS)
    assert len({raw for _, _, raw in attempts}) == 1


@pytest.mark.parametrize("error", [PermissionError(errno.EACCES, "No Windows code"),
    _windows_error(87), OSError(errno.EIO, "Unrelated I/O error")])
def test_unrelated_commit_errors_propagate_without_retry(monkeypatch, tmp_path, error):
    store = checkpoints.CheckpointStore(tmp_path)
    store.save(_record(1))
    target = tmp_path / "checkpoint-test.json"
    before = target.read_bytes()
    attempts, sleeps = [], []

    def denied(*args):
        attempts.append(args)
        raise error

    monkeypatch.setattr(checkpoints, "_replace", denied)
    monkeypatch.setattr(checkpoints, "_sleep", sleeps.append)
    with pytest.raises(type(error)) as failure:
        store.save(_record(2))
    assert failure.value is error
    assert len(attempts) == 1 and sleeps == []
    assert target.read_bytes() == before
    pending = list(tmp_path.glob("*.pending"))
    assert len(pending) == 1 and json.loads(pending[0].read_bytes())["token_count"] == 2


def test_non_permission_oserror_with_windows_code_is_not_retried(monkeypatch, tmp_path):
    store = checkpoints.CheckpointStore(tmp_path)
    error = OSError(errno.EIO, "Injected non-permission I/O error")
    error.winerror = 5
    attempts, sleeps = [], []
    def denied(*args):
        attempts.append(args)
        raise error
    monkeypatch.setattr(checkpoints, "_replace", denied)
    monkeypatch.setattr(checkpoints, "_sleep", sleeps.append)
    with pytest.raises(OSError) as failure:
        store.save(_record())
    assert failure.value is error and len(attempts) == 1 and sleeps == []


def test_serialization_failure_does_not_allocate_or_replace_snapshot(monkeypatch, tmp_path):
    store = checkpoints.CheckpointStore(tmp_path)
    store.save(_record(1))
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    record = _record(2)
    monkeypatch.setattr(record, "asdict", lambda: {"unsupported": object()})
    monkeypatch.setattr(checkpoints, "_replace", lambda *a: pytest.fail("Serialization failure reached commit"))
    monkeypatch.setattr(checkpoints, "_sleep", lambda *a: pytest.fail("Serialization failure retried"))
    with pytest.raises(TypeError):
        store.save(record)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_write_failure_closes_writer_and_preserves_prior_checkpoint(monkeypatch, tmp_path):
    store = checkpoints.CheckpointStore(tmp_path)
    store.save(_record(1))
    target = tmp_path / "checkpoint-test.json"
    prior = target.read_bytes()
    original_fdopen = checkpoints.os.fdopen
    opened = []
    error = OSError(errno.ENOSPC, "Injected disk full")

    class BrokenWriter:
        def __init__(self, stream):
            self.stream = stream
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.stream.close()
        def write(self, raw):
            raise error

    def fdopen(*args, **kwargs):
        stream = original_fdopen(*args, **kwargs)
        opened.append(stream)
        return BrokenWriter(stream)

    monkeypatch.setattr(checkpoints.os, "fdopen", fdopen)
    monkeypatch.setattr(checkpoints, "_replace", lambda *a: pytest.fail("Disk full reached commit"))
    monkeypatch.setattr(checkpoints, "_sleep", lambda *a: pytest.fail("Disk full retried"))
    with pytest.raises(OSError) as failure:
        store.save(_record(2))
    assert failure.value is error and all(stream.closed for stream in opened)
    assert target.read_bytes() == prior
    assert len(list(tmp_path.glob("*.pending"))) == 1


def test_fsync_failure_preserves_prior_checkpoint_without_commit(monkeypatch, tmp_path):
    store = checkpoints.CheckpointStore(tmp_path)
    store.save(_record(1))
    target = tmp_path / "checkpoint-test.json"
    prior = target.read_bytes()
    error = OSError(errno.EIO, "Injected durability failure")
    calls = []
    def failed_sync(fd):
        calls.append(fd)
        raise error
    monkeypatch.setattr(checkpoints.os, "fsync", failed_sync)
    monkeypatch.setattr(checkpoints, "_replace", lambda *a: pytest.fail("Failed fsync reached commit"))
    monkeypatch.setattr(checkpoints, "_sleep", lambda *a: pytest.fail("Failed fsync retried"))
    with pytest.raises(OSError) as failure:
        store.save(_record(2))
    assert failure.value is error and len(calls) == 1
    assert target.read_bytes() == prior
    pending = list(tmp_path.glob("*.pending"))
    assert len(pending) == 1 and json.loads(pending[0].read_bytes())["token_count"] == 2


def test_separate_failed_saves_never_overwrite_an_existing_pending_snapshot(monkeypatch, tmp_path):
    store = checkpoints.CheckpointStore(tmp_path)
    store.save(_record(1))
    monkeypatch.setattr(checkpoints, "_replace", lambda *a: (_ for _ in ()).throw(_windows_error()))
    monkeypatch.setattr(checkpoints, "_sleep", lambda seconds: None)
    with pytest.raises(checkpoints.CheckpointWriteError) as first:
        store.save(_record(2))
    first_raw = first.value.pending_path.read_bytes()
    with pytest.raises(checkpoints.CheckpointWriteError) as second:
        store.save(_record(3))
    assert first.value.pending_path != second.value.pending_path
    assert first.value.pending_path.read_bytes() == first_raw
    assert json.loads(second.value.pending_path.read_bytes())["token_count"] == 3
    assert store.get("checkpoint-test").token_count == 1


@pytest.mark.parametrize("run_id", ["../escape", "absolute/path", "C:\\target", "", None])
def test_unsafe_run_identifier_fails_without_allocating_snapshot(tmp_path, run_id):
    store = checkpoints.CheckpointStore(tmp_path)
    record = _record()
    record.run_id = run_id
    with pytest.raises(ValueError, match="Unsafe checkpoint run ID"):
        store.save(record)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(sys.platform != "win32", reason="Native Windows sharing-lock regression")
def test_native_windows_delete_sharing_lock_is_released_during_commit_retry(monkeypatch, tmp_path):
    from ctypes import wintypes
    store = checkpoints.CheckpointStore(tmp_path)
    store.save(_record(1))
    target = tmp_path / "checkpoint-test.json"
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    # Read sharing is permitted; FILE_SHARE_DELETE deliberately is not.
    handle = kernel.CreateFileW(str(target), 0x80000000, 1, None, 3, 0x80, None)
    assert handle is not None and handle != ctypes.c_void_p(-1).value, ctypes.get_last_error()
    mutex, close_errors = threading.Lock(), []

    def release():
        nonlocal handle
        with mutex:
            if handle is not None:
                if not kernel.CloseHandle(handle):
                    close_errors.append(ctypes.get_last_error())
                handle = None

    timer = threading.Timer(0.12, release)
    started = False
    original_replace = checkpoints._replace
    attempts = []

    def commit(pending, destination):
        nonlocal started
        attempts.append((pending, destination))
        try:
            return original_replace(pending, destination)
        except PermissionError:
            if not started:
                timer.start()
                started = True
            raise

    monkeypatch.setattr(checkpoints, "_replace", commit)
    try:
        store.save(_record(2))
        assert len(attempts) >= 2
        assert store.get("checkpoint-test").token_count == 2
        assert not list(tmp_path.glob("*.pending"))
    finally:
        timer.cancel()
        if started:
            timer.join(timeout=1.0)
        release()
    assert not close_errors
