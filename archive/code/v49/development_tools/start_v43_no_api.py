#!/usr/bin/env python3
"""Run tests, prepare a fresh comparison, and dry-run it. Never execute API mode.

Use the existing Windows virtualenv interpreter. Existing experiments and the
frozen reference are read-only sources. The output directory must be new.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from _score_core import code_tree_hash
from prepare_v43 import EXPECTED_V43_CODE_SHA256


def main():
    local = Path(os.environ["LOCALAPPDATA"]) if os.environ.get("LOCALAPPDATA") else None
    def default(relative: str):
        return local/relative if local is not None else None
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-api", type=Path, default=default("ER1287Eval_API01"))
    parser.add_argument("--original-offline", type=Path, default=default("ER1287Eval_Offline01"))
    parser.add_argument("--frozen", type=Path,
                        default=default("ER1287Gold")/"KEP1287_Reviewer_Confirmed_Freeze" if local else None)
    parser.add_argument("--previous-v42", type=Path, default=default("ER1287Eval_v42_GPT6_01"))
    parser.add_argument("--evaluation", type=Path,
                        help="Optional explicitly NEW output directory; otherwise choose unused LOCALAPPDATA name")
    args = parser.parse_args()
    code = Path(__file__).resolve().parent.parent
    if code_tree_hash(code) != EXPECTED_V43_CODE_SHA256:
        raise ValueError("v4.3 Python source differs from the tested package")
    sources = {
        "--original-api": (args.original_api, "RUN_RECEIPT.json"),
        "--original-offline": (args.original_offline, "score/metrics.json"),
        "--frozen": (args.frozen, "FREEZE_MANIFEST.json"),
        "--previous-v42": (args.previous_v42, "RUN_RECEIPT.json"),
    }
    for flag, (folder, sentinel) in sources.items():
        if folder is None or not (folder/sentinel).is_file():
            raise FileNotFoundError(f"Supply {flag}: expected existing {sentinel} under {folder}")
    evaluation = args.evaluation
    if evaluation is None:
        if local is None:
            parser.error("--evaluation is required outside Windows LOCALAPPDATA")
        number = 1
        while (local/f"ER1287Eval_v43Dev{number:02d}").exists():
            number += 1
        evaluation = local/f"ER1287Eval_v43Dev{number:02d}"
    evaluation = evaluation.resolve()
    if evaluation.exists():
        raise FileExistsError(f"Refuse overwriting existing evaluation: {evaluation}")
    child_environment = os.environ.copy()
    child_environment["PYTHONUTF8"] = "1"
    def run(*arguments):
        subprocess.run([sys.executable, *map(str, arguments)], cwd=code,
                       env=child_environment, check=True)
    print("v4.3 local tests and preparation only; no provider call will be made.", flush=True)
    run("-m", "pytest", "-q")
    run(code/"development_tools"/"prepare_v43.py",
        "--original-api", args.original_api, "--original-offline", args.original_offline,
        "--frozen", args.frozen, "--code-root", code, "--output", evaluation,
        "--models-from-evaluation", args.previous_v42)
    run(code/"development_tools"/"run_v43.py", "--evaluation", evaluation,
        "--code-root", code, "--dry-run")
    print(json.dumps({"status": "V43_TESTS_AND_DRY_RUN_COMPLETED_NO_API_CALLED",
                      "code_root": str(code), "evaluation": str(evaluation)}, indent=2))


if __name__ == "__main__":
    main()
