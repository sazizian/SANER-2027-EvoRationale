#!/usr/bin/env python3
"""Verify preserved development results without network access or provider calls.

The default operation is read-only. --write-summary regenerates only the two
derived summary files, after every source identity and rescoring check passes.
Hashes establish the supplied artifacts' consistency, not external authenticity
or the correctness of a model's semantic judgments.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile
import zipfile


class VerificationError(ValueError):
    """A preserved input, output, or derived measurement failed verification."""


SCORER_SHA256 = "18553a3a195a490102348e199233ef4ae752efaf8b80e351e52ff354c6d88895"
RESULTS_PATH = "data/results"
INDEX_PATH = f"{RESULTS_PATH}/index.json"
FROZEN_REFERENCE_PATH = "data/references/frozen_reference"
EXPECTED_LABELS = (
    "v4.4", "v4.5", "v4.6", "v4.7", "v4.8", "v4.9", "cached scope recheck"
)
SCOPES = ("baseline", "all")
METRIC_KEYS = (
    "scope", "evaluated_hunks", "gold_positive_exact_triples",
    "predicted_exact_triples", "tp", "fp", "fn", "precision", "recall", "f1",
    "predicted_hunk_coverage", "fp_on_unrelated_or_implementation_only_hunks",
    "unscored_prediction_links_outside_hunk_universe",
)
CSV_COLUMNS = (
    "run_label", "run_id", "scope", "tp", "fp", "fn", "precision", "recall",
    "f1", "evaluated_hunks", "gold_positive_exact_triples",
    "predicted_exact_triples", "evidence_class", "metric_status",
    "metrics_path", "model", "classification_status",
)


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        return json.load(stream)


def normalized_relative(value):
    require(isinstance(value, str) and bool(value), "Missing relative member path")
    normalized = value.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    require(not normalized.startswith("/") and bool(parts)
            and not any(x in (".", "..") or ":" in x for x in parts),
            f"Unsafe relative member path: {value!r}")
    return PurePosixPath(*parts).as_posix()


def repository_path(root, value):
    relative = normalized_relative(value)
    path = (root / relative).resolve()
    require(path.is_relative_to(root), f"Path escapes export root: {value!r}")
    return path


def checked_file(root, value, expected):
    path = repository_path(root, value)
    require(path.is_file(), f"Missing preserved file: {value}")
    require(digest(path) == expected, f"SHA-256 mismatch: {value}")
    return path


def core_hash(root):
    """The original release's path-and-content Python tree digest algorithm."""
    paths = sorted((root / "evorationale").rglob("*.py"))
    require(bool(paths), f"Missing EvoRationale Python source tree: {root}")
    h = hashlib.sha256()
    for path in paths:
        require(path.resolve().is_relative_to(root.resolve()),
                f"Source link escapes code root: {path}")
        relative = path.relative_to(root).as_posix().encode("utf-8")
        h.update(len(relative).to_bytes(4, "big") + relative)
        h.update(bytes.fromhex(digest(path)))
    return h.hexdigest()


def checked_zip(path, expected_digest):
    require(digest(path) == expected_digest,
            f"Diagnostic ZIP SHA-256 mismatch: {path.name}")
    members = {}
    with zipfile.ZipFile(path) as archive:
        require(archive.testzip() is None, f"Diagnostic ZIP CRC failure: {path.name}")
        for item in archive.infolist():
            if item.is_dir():
                continue
            name = normalized_relative(item.filename)
            require(name not in members, f"Duplicate diagnostic ZIP member: {name}")
            members[name] = hashlib.sha256(archive.read(item)).hexdigest()
    return members


def load_scorer(root, index):
    require(index["unchanged_scorer_sha256"] == SCORER_SHA256,
            "Catalog does not pin the unchanged exact-triple scorer")
    path = checked_file(root, "development_tools/_score_core.py", SCORER_SHA256)
    # Prevent importing even stdlib bytecode into the read-only export.
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location("_export_preserved_scorer", path)
        require(spec is not None and spec.loader is not None, "Cannot load scorer")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def check_frozen_reference(root, index):
    frozen = repository_path(root, index["exported_frozen_reference_path"])
    members = index["required_frozen_reference_export_members"]
    require(len(members) == 7 and index["required_frozen_reference_export_member_count"] == 7,
            "Expected the seven preserved frozen-reference files")
    names = set()
    for item in members:
        name = normalized_relative(item["member"])
        require(name not in names, "Duplicate frozen-reference member")
        names.add(name)
        path = checked_file(root, item["exported_path"], item["sha256"])
        require(path == frozen / name, f"Frozen-reference path/member mismatch: {name}")
    manifest_path = frozen / "FREEZE_MANIFEST.json"
    require(digest(manifest_path) == index["frozen_manifest_sha256"],
            "Frozen manifest identity differs from the results catalog")
    manifest = read_json(manifest_path)
    require(digest(frozen / "S0_ATOMIC_REVIEWER_CONFIRMED.json") == manifest["s0_sha256"],
            "Frozen S0 does not match its freeze manifest")
    for name, expected in manifest["reference_sha256"].items():
        relative = normalized_relative(name)
        path = frozen / "reference" / relative
        require(path.is_file() and digest(path) == expected,
                f"Frozen reference CSV does not match manifest: {relative}")
    hunk_path = frozen / "reference" / "HUNK_RELATIONS_CANDIDATE.csv"
    with hunk_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 30 and len({r["hunk_id"] for r in rows}) == 30,
            "Expected exactly 30 unique preserved hunk judgments")
    return rows, manifest


def compare_rescoring(scorer, gold, report, metrics, errors_path, label):
    errors = []
    for scope in SCOPES:
        actual, actual_errors = scorer.evaluate(gold, report, scope)
        stored = metrics["results"][scope]
        for key in METRIC_KEYS:
            require(stored.get(key) == actual.get(key),
                    f"Recomputed score differs: {label}/{scope}/{key}")
        require(actual["evaluated_hunks"] == (24 if scope == "baseline" else 30),
                f"Unexpected hunk universe: {label}/{scope}")
        require(actual["gold_positive_exact_triples"] == (14 if scope == "baseline" else 19),
                f"Unexpected positive triple population: {label}/{scope}")
        errors.extend({k: str(v) for k, v in row.items()} for row in actual_errors)
    with errors_path.open(encoding="utf-8-sig", newline="") as stream:
        saved_errors = list(csv.DictReader(stream))
    key = lambda row: json.dumps(row, sort_keys=True, ensure_ascii=True)
    require(collections.Counter(map(key, saved_errors)) == collections.Counter(map(key, errors)),
            f"Recomputed TP/FP/FN CSV rows differ: {label}")


def verify_run(root, record, scorer, gold, freeze_manifest):
    label = record["label"]
    run_root = repository_path(root, record["exported_run_path"])
    members = record["original_diagnostic_members"]
    require(bool(members), f"No diagnostic members declared for {label}")
    declared = {}
    for item in members:
        name = normalized_relative(item["member"])
        require(name not in declared, f"Duplicate catalog run member: {label}/{name}")
        path = checked_file(root, item["exported_path"], item["sha256"])
        require(path == run_root / name, f"Run path/member mismatch: {label}/{name}")
        declared[name] = item["sha256"]
    zip_path = repository_path(root, record["exported_raw_zip_path"])
    require(zip_path.is_file(), f"Missing diagnostic ZIP for {label}")
    zip_members = checked_zip(zip_path, record["raw_upload_zip_sha256"])
    require(zip_members == declared,
            f"Diagnostic ZIP and exported member set differ: {label}")

    manifest_path = run_root / "DIAGNOSTIC_BUNDLE_MANIFEST.json"
    partial = label == "v4.4"
    if partial:
        require(not manifest_path.exists() and len(declared) == 7,
                "v4.4 must retain its original seven-file partial-provenance snapshot")
        expected_class = "UPLOADED_FLAT_DIAGNOSTIC_ZIP_RECEIPT_LINKED_PARTIAL_PROVENANCE"
    else:
        require(manifest_path.is_file(), f"Missing original member manifest for {label}")
        manifest = read_json(manifest_path)
        authority = {normalized_relative(k): v for k, v in manifest["member_sha256"].items()}
        require(authority == {k: v for k, v in declared.items()
                              if k != "DIAGNOSTIC_BUNDLE_MANIFEST.json"},
                f"Original member manifest differs from exported files: {label}")
        require(manifest["run_id"] == record["run_id"],
                f"Bundle manifest run UUID differs: {label}")
        expected_class = "COMPLETE_DECLARED_DIAGNOSTIC_MEMBERS_HASH_VERIFIED"
    require(record["evidence_class"] == expected_class,
            f"Catalog provenance class is incorrect: {label}")

    receipt_path = repository_path(root, record["exported_receipt_path"])
    report_path = repository_path(root, record["exported_report_path"])
    metrics_path = repository_path(root, record["exported_metrics_path"])
    checkpoint_path = repository_path(root, record["exported_checkpoint_path"])
    for path in (receipt_path, report_path, metrics_path, checkpoint_path):
        require(path.is_relative_to(run_root) and path.relative_to(run_root).as_posix() in declared,
                f"Identity path is outside declared original members: {label}/{path.name}")
    receipt = read_json(receipt_path)
    report = read_json(report_path)
    metrics = read_json(metrics_path)
    checkpoint = read_json(checkpoint_path)
    require(receipt["run_id"] == record["run_id"] == checkpoint["run_id"],
            f"Receipt/checkpoint/catalog UUID mismatch: {label}")
    require(receipt["mode"] == "api", f"Not a preserved hosted observation: {label}")
    require(digest(report_path) == receipt["run_report_sha256"],
            f"Run report differs from completed-run receipt: {label}")
    require(metrics["frozen_s0_sha256"] == freeze_manifest["s0_sha256"],
            f"Metrics used a different frozen S0: {label}")
    if not partial:
        require(digest(checkpoint_path) == receipt["checkpoint_sha256"],
                f"Checkpoint differs from completed-run receipt: {label}")
        run_manifest_path = run_root / "run" / "manifest.json"
        require(digest(run_manifest_path) == receipt["run_manifest_sha256"],
                f"Run manifest differs from receipt: {label}")
        run_manifest = read_json(run_manifest_path)
        require(run_manifest["run_id"] == receipt["run_id"],
                f"Run manifest UUID differs from receipt: {label}")
        require(run_manifest["report_sha256"] == digest(report_path),
                f"Run manifest report identity differs: {label}")
        if label.startswith("v4."):
            for key, filename in (("decision_sha256", "S0_RETROSPECTIVE_RUNTIME.json"),
                                  ("history_sha256", "POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl")):
                require(run_manifest[key] == digest(run_root / "inputs" / filename),
                        f"Run manifest input identity differs: {label}/{filename}")

    source_hash = None
    if label.startswith("v4."):
        version = label.replace("v4.", "v4")
        code_root = repository_path(root, f"archive/code/{version}")
        source_hash = core_hash(code_root)
        require(source_hash == receipt["code_tree_sha256"],
                f"Historical code tree differs from hosted-run receipt: {label}")
        if label == "v4.9":
            require(core_hash(root) == source_hash,
                    "Active root v4.9 core differs from preserved v4.9 hosted code")
    else:
        protocol_path = run_root / "PROTOCOL.json"
        require(digest(protocol_path) == receipt["protocol_sha256"],
                "Scope protocol differs from completed-run receipt")
        protocol = read_json(protocol_path)
        require(run_manifest["protocol_sha256"] == receipt["protocol_sha256"],
                "Scope run manifest protocol identity differs")
        for key, filename in (("runtime_s0_sha256", "S0_RETROSPECTIVE_RUNTIME.json"),
                              ("history_sha256", "POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl"),
                              ("source_checkpoint_sha256", "V49_PRIMARY_CHECKPOINT.json")):
            require(protocol[key] == digest(run_root / "inputs" / filename),
                    f"Scope protocol input identity differs: {filename}")
        require(protocol["source_core_sha256"] == core_hash(root),
                "Scope cached primary core differs from active v4.9 core")
        require(receipt["source_run_id"] == record["source_run_id"],
                "Scope cached primary run identity differs")
        require(report["new_primary_api_requests"] == 0,
                "Scope recheck must not claim a fresh primary classification")

    errors_path = run_root / ("link_errors.csv" if partial else "score/link_errors.csv")
    compare_rescoring(scorer, gold, report, metrics, errors_path, label)
    for scope in SCOPES:
        catalog_score = record["results"][scope]
        for key in METRIC_KEYS:
            if key != "scope":
                require(catalog_score.get(key) == metrics["results"][scope].get(key),
                        f"Catalog differs from raw score: {label}/{scope}/{key}")
    audit = {
        "run_label": label, "run_id": receipt["run_id"],
        "original_members_verified": len(declared), "zip_crc_and_sha256_verified": True,
        "evidence_class": expected_class, "scopes_reproduced": list(SCOPES),
        "all_error_csv_rows_reproduced": True,
        "historical_core_sha256": source_hash,
        "missing_original_provenance_files": record["missing_original_provenance_files"],
    }
    model = receipt.get("model")
    if isinstance(model, dict):
        model = "; ".join(f"{key}={value}" for key, value in sorted(model.items()))
    rows = []
    for scope in SCOPES:
        raw = metrics["results"][scope]
        row = {key: raw[key] for key in CSV_COLUMNS if key in raw}
        row.update({
            "run_label": label, "run_id": receipt["run_id"], "scope": scope,
            "evidence_class": expected_class,
            "metric_status": "OBSERVED_DEVELOPMENT_LINK_SCORE",
            "metrics_path": record["exported_metrics_path"], "model": model,
            "classification_status": "CACHED_V49_PRIMARY_RECHECK" if not source_hash
            else "COMPLETED_HOSTED_DEVELOPMENT_RUN",
        })
        rows.append(row)
    return audit, rows


def verify_repository(root):
    root = Path(root).resolve()
    index = read_json(repository_path(root, INDEX_PATH))
    require(index["exported_frozen_reference_path"] == FROZEN_REFERENCE_PATH,
            "Frozen-reference catalog path must use data/references/frozen_reference")
    records = index["hosted_development_runs"]
    require(tuple(r["label"] for r in records) == EXPECTED_LABELS,
            "Expected the seven preserved development run records in fixed order")
    for record in records:
        require(normalized_relative(record["exported_run_path"]).startswith(f"{RESULTS_PATH}/runs/"),
                f"Run catalog path must use data/results/runs: {record['label']}")
    scorer = load_scorer(root, index)
    gold, freeze_manifest = check_frozen_reference(root, index)
    known = set(scorer.KNOWN)
    require(all(row["relation_candidate"] in known for row in gold),
            "Unknown relation in frozen reference")
    run_audits, rows = [], []
    for record in records:
        audit, run_rows = verify_run(root, record, scorer, gold, freeze_manifest)
        run_audits.append(audit)
        rows.extend(run_rows)

    latest = index["latest_primary_effect_experiment"]
    require(latest["hosted_accuracy_available"] is False
            and latest["hosted_run_id"] is None and latest["f1"] is None,
            "This snapshot has no PrimaryEffects hosted result; do not invent accuracy")
    pending = {key: None for key in CSV_COLUMNS}
    pending.update({
        "run_label": latest["label"], "scope": "pending",
        "evidence_class": "LOCAL_VALIDATION_ONLY_HOSTED_RUN_PENDING",
        "metric_status": "PENDING_NO_HOSTED_ACCURACY",
        "classification_status": "LOCAL_TESTS_AND_MOCK_FORECAST_ONLY",
    })
    rows.append(pending)
    summary = {
        "status": "VERIFIED_DEVELOPMENT_RESULTS_NO_API_CALLED",
        "provider_requests_made": 0, "hosted_runs_verified": len(run_audits),
        "scored_scope_rows": len(rows) - 1, "primary_hosted_accuracy_available": False,
        "rows": rows, "limitations": index["limitations"],
    }
    audit = {
        "status": "VERIFIED_DEVELOPMENT_RESULTS_NO_API_CALLED",
        "provider_requests_made": 0, "read_only_default": True,
        "unchanged_scorer_sha256": SCORER_SHA256,
        "frozen_reference_members_verified": 7,
        "hosted_runs_verified": len(run_audits),
        "original_diagnostic_members_verified": sum(r["original_members_verified"] for r in run_audits),
        "scored_scope_rows_reproduced": len(rows) - 1,
        "primary_hosted_accuracy_available": False,
        "legacy_comparison_only_values_not_rescored": len(index["legacy_comparison_only_values"]["entries"]),
        "runs": run_audits,
        "note": "Artifact consistency and exact-triple rescoring; no held-out or outcome accuracy established.",
    }
    return audit, summary


def summary_bytes(summary):
    encoded_json = (json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(summary["rows"])
    return encoded_json, stream.getvalue().encode("utf-8")


def write_summaries(root, summary):
    json_bytes, csv_bytes = summary_bytes(summary)
    results = repository_path(Path(root).resolve(), RESULTS_PATH)
    for name, content in (("summary.json", json_bytes), ("summary.csv", csv_bytes)):
        target = results / name
        descriptor, temporary = tempfile.mkstemp(prefix=f".{name}.", suffix=".tmp", dir=results)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Export repository root (default: this script's parent repository)")
    parser.add_argument("--write-summary", action="store_true",
                        help="Regenerate only data/results/summary.json and summary.csv after all checks pass")
    args = parser.parse_args(argv)
    try:
        audit, summary = verify_repository(args.root)
        if args.write_summary:
            write_summaries(args.root, summary)
            audit["generated_summary_files"] = [f"{RESULTS_PATH}/summary.json", f"{RESULTS_PATH}/summary.csv"]
        print(json.dumps(audit, indent=2, sort_keys=True, ensure_ascii=True))
        return 0
    except (VerificationError, OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
