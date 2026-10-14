#!/usr/bin/env python3
"""Verify the central data resource catalog without modifying files or calling APIs.

Source resources retain their original bytes. The CSV and JSON inventories must
agree, canonical model inputs must match the preserved v4.9 run, and Excel Open
XML workbooks must pass ZIP integrity checks. This does not validate spreadsheet
judgments or establish model accuracy.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile


CATALOG_KIND = "EVORATIONALE_CENTRAL_DATA_RESOURCE_INDEX"
CATALOG_COLUMNS = (
    "path", "role", "status", "source_path", "size_bytes", "sha256", "byte_preserved"
)
INPUT_DIRECTORY = "data/inputs/kep1287"
INPUT_FILENAMES = (
    "S0_RETROSPECTIVE_RUNTIME.json", "POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl"
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def data_member(root, value):
    require(isinstance(value, str) and bool(value) and "\\" not in value,
            "Unsafe data resource path")
    relative = PurePosixPath(value)
    require(not relative.is_absolute() and relative.parts and relative.parts[0] == "data"
            and not any(part in (".", "..") or ":" in part for part in relative.parts),
            "Unsafe data resource path")
    path = root.joinpath(*relative.parts)
    require(not path.is_symlink() and path.is_file() and path.resolve().is_relative_to(root),
            f"Missing/nonregular data resource: {value}")
    return path


def verify_data(root):
    root = Path(root).resolve()
    catalog = json.loads((root / "data/RESOURCE_INDEX.json").read_text(encoding="utf-8"))
    require(catalog.get("catalog_kind") == CATALOG_KIND, "Unexpected data resource catalog")
    require(catalog.get("source_files_are_byte_preserved") is True,
            "Data catalog must declare original source byte preservation")
    require(catalog.get("reference_labels_are_post_run_scoring_only") is True,
            "Reference labels must remain post-run scoring resources")
    entries = catalog["entries"]
    require(isinstance(entries, list) and bool(entries), "Empty data resource catalog")
    declared = {}
    excel_count = 0
    for item in entries:
        require(isinstance(item, dict) and set(item) == set(CATALOG_COLUMNS),
                "Unexpected data resource entry fields")
        relative = item["path"]
        path = data_member(root, relative)
        require(relative not in declared, f"Duplicate data resource path: {relative}")
        require(item["byte_preserved"] is True, f"Source bytes not preserved: {relative}")
        require(type(item["size_bytes"]) is int and item["size_bytes"] >= 0,
                f"Invalid data resource size: {relative}")
        require(all(isinstance(item[key], str) and bool(item[key])
                    for key in ("role", "status", "source_path", "sha256")),
                f"Missing data resource provenance: {relative}")
        require(path.stat().st_size == item["size_bytes"], f"Data resource size differs: {relative}")
        require(file_digest(path) == item["sha256"], f"Data resource SHA-256 differs: {relative}")
        if path.suffix.lower() in (".xlsx", ".xlsm", ".xltx", ".xltm"):
            with zipfile.ZipFile(path) as workbook:
                require(workbook.testzip() is None, f"Excel ZIP CRC failure: {relative}")
                names = workbook.namelist()
                require(len(names) == len(set(names)), f"Duplicate Excel ZIP member: {relative}")
                require("[Content_Types].xml" in names and "xl/workbook.xml" in names,
                        f"Missing Excel workbook structure: {relative}")
            excel_count += 1
        declared[relative] = item

    with (root / "data/RESOURCE_INDEX.csv").open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames is not None and len(reader.fieldnames) == len(CATALOG_COLUMNS)
                and set(reader.fieldnames) == set(CATALOG_COLUMNS),
                "Resource CSV columns differ from JSON inventory")
        csv_rows = list(reader)
    require(all(set(row) == set(CATALOG_COLUMNS) and None not in row.values() for row in csv_rows),
            "Malformed resource CSV row")
    expected_rows = [{key: str(item[key]) for key in CATALOG_COLUMNS} for item in entries]
    identity = lambda row: json.dumps(row, sort_keys=True, ensure_ascii=True)
    require(collections.Counter(map(identity, csv_rows)) == collections.Counter(map(identity, expected_rows)),
            "Resource CSV rows differ from JSON inventory")

    results = json.loads((root / "data/results/index.json").read_text(encoding="utf-8"))
    v49 = [record for record in results["hosted_development_runs"] if record["label"] == "v4.9"]
    require(len(v49) == 1, "Expected one preserved v4.9 run identity")
    original_inputs = {item["member"]: item for item in v49[0]["original_diagnostic_members"]
                       if item["member"].startswith("inputs/")}
    for filename in INPUT_FILENAMES:
        relative = f"{INPUT_DIRECTORY}/{filename}"
        require(relative in declared, f"Missing canonical input resource: {filename}")
        item = declared[relative]
        require(item["role"] == "fixed_unlabeled_runtime_input" and item["status"] == "CONFIRMED_RUN_INPUT",
                f"Canonical input has an incorrect catalog role: {filename}")
        preserved = original_inputs[f"inputs/{filename}"]
        original = data_member(root, preserved["exported_path"])
        require(file_digest(original) == preserved["sha256"] == item["sha256"],
                f"Canonical model input differs from preserved v4.9 input: {filename}")
    history = data_member(root, f"{INPUT_DIRECTORY}/{INPUT_FILENAMES[1]}")
    rows = [json.loads(line) for line in history.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    require(len(rows) == 53 and len({row["artifact_id"] for row in rows}) == 53,
            "Canonical history must retain exactly 53 unique artifacts")

    return {
        "status": "CENTRAL_DATA_RESOURCES_VERIFIED_NO_API_CALLED",
        "provider_requests_made": 0, "read_only": True,
        "resource_files_verified": len(entries), "json_csv_inventory_agreement": True,
        "excel_workbook_zip_integrity_checks": excel_count,
        "canonical_model_inputs_match_preserved_v49": True,
        "canonical_history_artifact_count": 53,
        "reference_labels_are_post_run_scoring_only": True,
        "note": "Resource byte consistency; no spreadsheet judgment or model accuracy is certified.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        print(json.dumps(verify_data(args.root), indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
