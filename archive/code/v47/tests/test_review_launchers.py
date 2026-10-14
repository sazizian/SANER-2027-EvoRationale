"""Regression checks for launcher cwd changes and exclusive hosted attempts.

All provider work is replaced by explicit local transport fixtures. Preparation
and dry-run subprocesses run against synthetic hashed comparison inputs.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from threading import Event, Thread

import pytest

from test_v44_development_tools import (
    ROOT, command, prepared_inputs, sha, write,
)


def load_tool(name, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "development_tools"))
    spec = importlib.util.spec_from_file_location(
        "launcher_review_" + name, ROOT / "development_tools" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_relative_paths_survive_package_cwd_with_spaces_and_unicode(
    prepared_inputs, monkeypatch, tmp_path, capsys,
):
    api, offline, frozen, parent, *_ = prepared_inputs
    caller = tmp_path / "caller folder caf\u00e9"
    caller.mkdir()
    source_paths = {}
    for flag, source in (("--original-api", api), ("--original-offline", offline),
                         ("--frozen", frozen), ("--previous-v43", parent)):
        destination = caller / (source.name + " copied r\u00e9sum\u00e9")
        shutil.copytree(source, destination)
        source_paths[flag] = destination
    before = {path: sha(path) for folder in source_paths.values()
              for path in folder.rglob("*") if path.is_file()}
    evaluation = caller / "new output na\u00efve"
    module = load_tool("start_v44_no_api", monkeypatch)
    from _score_core import code_tree_hash
    monkeypatch.setattr(module, "EXPECTED_V44_CODE_SHA256", code_tree_hash(ROOT))
    actual_run = subprocess.run
    commands = []

    def local_subprocess(arguments, **kwargs):
        commands.append(arguments)
        assert kwargs["cwd"] == ROOT
        assert kwargs["env"]["PYTHONUTF8"] == "1"
        if arguments[1:4] == ["-m", "pytest", "-q"]:
            # Running pytest here would recurse into this same regression.
            return subprocess.CompletedProcess(arguments, 0)
        if Path(arguments[1]).name == "prepare_v44.py":
            # Only substitute this synthetic fixture's package-hash pin.
            wrapper = (
                f"import sys; sys.path.insert(0, {str(ROOT/'development_tools')!r}); "
                "import prepare_v44; from _score_core import code_tree_hash; "
                f"prepare_v44.EXPECTED_V44_CODE_SHA256 = code_tree_hash({str(ROOT)!r}); "
                "prepare_v44.main()"
            )
            arguments = [arguments[0], "-c", wrapper, *arguments[2:]]
        return actual_run(arguments, **kwargs, capture_output=True, text=True)

    monkeypatch.setattr(module.subprocess, "run", local_subprocess)
    monkeypatch.chdir(caller)
    argv = ["start_v44_no_api.py"]
    for flag, folder in source_paths.items():
        argv.extend([flag, folder.name])
    argv.extend(["--evaluation", evaluation.name])
    monkeypatch.setattr(sys, "argv", argv)
    module.main()
    assert len(commands) == 3
    prepare_command = commands[1]
    for flag, folder in source_paths.items():
        assert prepare_command[prepare_command.index(flag) + 1] == str(folder.resolve())
    assert (evaluation / "DEV_PREP_MANIFEST.json").is_file()
    assert not (evaluation / "run").exists()
    assert not (evaluation / "RUN_ATTEMPT.json").exists()
    assert all(sha(path) == expected for path, expected in before.items())
    assert "V44_TESTS_AND_DRY_RUN_COMPLETED_NO_API_CALLED" in capsys.readouterr().out


def test_dry_run_cli_arguments_accept_opaque_models_and_budgets(prepared_inputs, monkeypatch):
    *_, evaluation, arguments, _ = prepared_inputs
    preparation = command("prepare_v44.py", arguments)
    assert preparation.returncode == 0, preparation.stderr
    dry = command("run_v44.py", ["--evaluation", evaluation, "--code-root", ROOT, "--dry-run"])
    assert dry.returncode == 0, dry.stderr
    invocation = json.loads(dry.stdout)["command"]
    config = json.loads((evaluation / "DEV_PREP_MANIFEST.json").read_text())
    assert invocation[invocation.index("--model") + 1] == config["models"]["linker"]
    assert invocation[invocation.index("--judge-model") + 1] == config["models"]["judge"]
    from evorationale import cli
    parsed_arguments = []
    monkeypatch.setattr(cli, "_run", parsed_arguments.append)
    monkeypatch.setattr(sys, "argv", ["evorationale", *invocation[3:]])
    cli.main()
    assert len(parsed_arguments) == 1
    parsed = parsed_arguments[0]
    assert parsed.investigation_profile == "event-complete"
    assert parsed.max_input_tokens == config["budgets"]["max_input_tokens"]
    assert parsed.decision == evaluation / "inputs" / "S0_RETROSPECTIVE_RUNTIME.json"


def prepared_runner(prepared_inputs, monkeypatch):
    *_, evaluation, arguments, _ = prepared_inputs
    preparation = command("prepare_v44.py", arguments)
    assert preparation.returncode == 0, preparation.stderr
    module = load_tool("run_v44", monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-untransmitted-key")
    monkeypatch.setattr(sys, "argv", ["run_v44.py", "--evaluation", str(evaluation),
                                      "--code-root", str(ROOT),
                                      "--i-approve-public-repository-excerpts-to-openai"])
    return module, evaluation


def test_concurrent_launchers_only_start_one_hosted_attempt(prepared_inputs, monkeypatch):
    module, evaluation = prepared_runner(prepared_inputs, monkeypatch)
    entered, release = Event(), Event()
    worker_errors = []
    calls = []
    cfg = json.loads((evaluation / "DEV_PREP_MANIFEST.json").read_text())

    def simulated_run(arguments, **kwargs):
        calls.append(arguments)
        assert kwargs["env"]["PYTHONUTF8"] == "1"
        entered.set()
        assert release.wait(10), "Local test worker was not released"
        write(evaluation / "run" / "report.json", {"verified_evidence": []})
        write(evaluation / "run" / "manifest.json", {
            "run_id": "synthetic-exclusive-attempt", "mode": "api",
            "investigation_profile": "event-complete",
            "decision_sha256": cfg["runtime_s0_sha256"], "history_sha256": cfg["history_sha256"],
            "report_sha256": sha(evaluation / "run" / "report.json"),
        })

    def worker():
        try:
            module.main()
        except BaseException as exc:
            worker_errors.append(exc)

    monkeypatch.setattr(module.subprocess, "run", simulated_run)
    thread = Thread(target=worker)
    thread.start()
    try:
        assert entered.wait(10), "Local test worker did not enter simulated run"
        # No run/checkpoint has been created yet, so the exclusive attempt is
        # the only protection against a second launch using the same inputs.
        assert not (evaluation / "run").exists()
        with pytest.raises(FileExistsError, match="Refuse overwriting"):
            module.main()
    finally:
        release.set()
        thread.join(10)
    assert not thread.is_alive()
    assert not worker_errors
    assert len(calls) == 1
    assert (evaluation / "RUN_RECEIPT.json").is_file()
    assert "synthetic-untransmitted-key" not in (evaluation / "RUN_ATTEMPT.json").read_text()


def test_failed_attempt_preserved_and_cannot_restart(prepared_inputs, monkeypatch):
    module, evaluation = prepared_runner(prepared_inputs, monkeypatch)
    calls = []

    def simulated_failure(arguments, **kwargs):
        calls.append(arguments)
        raise subprocess.CalledProcessError(1, arguments)

    monkeypatch.setattr(module.subprocess, "run", simulated_failure)
    with pytest.raises(subprocess.CalledProcessError):
        module.main()
    attempt = (evaluation / "RUN_ATTEMPT.json").read_bytes()
    assert not (evaluation / "RUN_RECEIPT.json").exists()
    with pytest.raises(FileExistsError, match="Refuse overwriting"):
        module.main()
    assert len(calls) == 1
    assert (evaluation / "RUN_ATTEMPT.json").read_bytes() == attempt


def test_preflight_checks_recovered_safe_subwindow_ranges(approved_state):
    from test_v44_no_api_audit import audit, source, MODELS, BUDGETS
    patch = "@@ -2,2 +2,2 @@\n-Old safe statement.\n+New safe statement.\n Contact user@example.com\n"
    result = audit.audit_sources(approved_state, [source(approved_state, content=patch)], MODELS, BUDGETS)
    batch = result["batches"][0]
    assert batch["recovered_safe_passages"] >= 1
    assert batch["exact_diff_handle_line_ranges_checked"] >= 1
    assert batch["outbound_safe_passages"] == batch["safely_quotable_source_passages"]
    coverage = batch["changed_line_coverage"][0]
    assert coverage["changed_source_lines"] == 2
    assert coverage["covered_changed_source_lines"] == 2
    assert coverage["covered_safely_quotable_changed_source_lines"] == 2
    assert coverage["unquoted_individually_unredacted_changed_source_lines"] == 0
    assert result["provider_calls"] == 0


@pytest.mark.parametrize("relative", ["DEV_PREP_MANIFEST.json", "inputs/POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl"])
def test_inputs_or_preparation_edited_during_attempt_cannot_receive_receipt(
    prepared_inputs, monkeypatch, relative,
):
    module, evaluation = prepared_runner(prepared_inputs, monkeypatch)

    def simulated_edit(arguments, **kwargs):
        write(evaluation / "run" / "report.json", {"verified_evidence": []})
        target = evaluation / relative
        target.write_bytes(target.read_bytes() + b"\n ")

    monkeypatch.setattr(module.subprocess, "run", simulated_edit)
    with pytest.raises(ValueError, match="Hash mismatch"):
        module.main()
    assert (evaluation / "run" / "report.json").is_file()
    assert (evaluation / "RUN_ATTEMPT.json").is_file()
    assert not (evaluation / "RUN_RECEIPT.json").exists()
