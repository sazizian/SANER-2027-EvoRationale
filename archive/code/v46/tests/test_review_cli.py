"""Direct CLI regressions: reject invalid inputs/occupied reports before work."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from evorationale import cli
from evorationale.model import ValidationError


def inputs(tmp_path, state, history):
    decision = tmp_path / "decision.json"
    captured = tmp_path / "history.jsonl"
    decision.write_text(json.dumps(state), encoding="utf-8")
    captured.write_text("".join(json.dumps(a) + "\n" for a in history), encoding="utf-8")
    return SimpleNamespace(decision=decision, history=captured, output=tmp_path / "run")


@pytest.mark.parametrize("existing", ["report.json", "trace.json", "data_audit.json", "manifest.json"])
def test_direct_run_never_overwrites_prior_experiment(tmp_path, approved_state, history, monkeypatch, existing):
    args = inputs(tmp_path, approved_state, history)
    args.output.mkdir()
    prior = args.output / existing
    prior.write_bytes(b"previous-experiment-bytes")
    called = []
    monkeypatch.setattr(cli, "build_agent", lambda a: called.append(a))
    with pytest.raises(FileExistsError, match="already contains"):
        cli._run(args)
    assert called == []
    assert prior.read_bytes() == b"previous-experiment-bytes"
    assert list(args.output.iterdir()) == [prior]


def test_direct_run_rejects_unapproved_state_before_constructing_agent(tmp_path, approved_state, history, monkeypatch):
    state = deepcopy(approved_state)
    state["human_approved"] = False
    args = inputs(tmp_path, state, history)
    called = []
    monkeypatch.setattr(cli, "build_agent", lambda a: called.append(a))
    with pytest.raises(ValidationError):
        cli._run(args)
    assert not called and not args.output.exists()


def test_direct_run_rejects_corrupt_history_before_constructing_agent(tmp_path, approved_state, history, monkeypatch):
    corrupted = deepcopy(history)
    corrupted[0]["content"] += " modified after capture"
    args = inputs(tmp_path, approved_state, corrupted)
    called = []
    monkeypatch.setattr(cli, "build_agent", lambda a: called.append(a))
    with pytest.raises(ValidationError):
        cli._run(args)
    assert not called and not args.output.exists()


def test_direct_run_checks_output_writeability_before_work(tmp_path, approved_state, history, monkeypatch):
    args = inputs(tmp_path, approved_state, history)
    args.output.write_bytes(b"not-a-directory")
    called = []
    monkeypatch.setattr(cli, "build_agent", lambda a: called.append(a))
    with pytest.raises(FileExistsError, match="must be a directory"):
        cli._run(args)
    assert not called and args.output.read_bytes() == b"not-a-directory"
