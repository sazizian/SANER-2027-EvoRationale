"""Read-only provenance/rescoring integration checks; no API or new accuracy."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile


EXPORT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("export_results_verifier", EXPORT / "tools/verify_results.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class VerifyResultsIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_index = VERIFY.read_json(EXPORT / "data/results/index.json")
        files = {Path("data/results/index.json"), Path("development_tools/_score_core.py")}
        for run in cls.source_index["hosted_development_runs"]:
            files.add(Path(run["exported_raw_zip_path"]))
            files.update(Path(item["exported_path"]) for item in run["original_diagnostic_members"])
        files.update(Path(item["exported_path"])
                     for item in cls.source_index["required_frozen_reference_export_members"])
        for code_root in [EXPORT] + [EXPORT / "archive/code" / f"v4{i}" for i in range(4, 10)]:
            files.update(path.relative_to(EXPORT) for path in (code_root / "evorationale").rglob("*.py"))
        cls.preserved_files = sorted(files)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="export_verify_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for relative in self.preserved_files:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(EXPORT / relative, destination)
        self.index_path = self.root / "data/results/index.json"
        self.index = VERIFY.read_json(self.index_path)

    def test_verified_snapshot_is_read_only_and_primary_remains_null(self):
        before = {p.relative_to(self.root): VERIFY.digest(p) for p in self.root.rglob("*") if p.is_file()}
        audit, summary = VERIFY.verify_repository(self.root)
        after = {p.relative_to(self.root): VERIFY.digest(p) for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(audit["hosted_runs_verified"], 7)
        self.assertEqual(audit["scored_scope_rows_reproduced"], 14)
        self.assertEqual(audit["original_diagnostic_members_verified"], 72)
        self.assertEqual(len(summary["rows"]), 15)
        self.assertEqual(summary["rows"][-1]["metric_status"], "PENDING_NO_HOSTED_ACCURACY")
        for key in ("tp", "fp", "fn", "precision", "recall", "f1"):
            self.assertIsNone(summary["rows"][-1][key])
        raw_v49 = VERIFY.read_json(self.root / "data/results/runs/v49/score/metrics.json")
        generated_v49 = next(row for row in summary["rows"]
                             if row["run_label"] == "v4.9" and row["scope"] == "all")
        self.assertEqual(generated_v49["f1"], raw_v49["results"]["all"]["f1"])
        self.assertIn("DIAGNOSTIC_BUNDLE_MANIFEST.json",
                      audit["runs"][0]["missing_original_provenance_files"])

    def test_summary_regeneration_is_deterministic_and_does_not_rewrite_index(self):
        index_hash = VERIFY.digest(self.index_path)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(VERIFY.main(["--root", str(self.root), "--write-summary"]), 0)
        first = {name: (self.root / "data/results" / name).read_bytes()
                 for name in ("summary.json", "summary.csv")}
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(VERIFY.main(["--root", str(self.root), "--write-summary"]), 0)
        for name, content in first.items():
            self.assertEqual(content, (self.root / "data/results" / name).read_bytes())
        self.assertEqual(index_hash, VERIFY.digest(self.index_path))
        self.assertFalse(list((self.root / "data/results").glob("*.tmp")))
        self.assertFalse((self.root / "results").exists())

    def test_legacy_results_directory_is_not_a_catalog_fallback(self):
        legacy = self.root / "results"
        legacy.mkdir()
        shutil.copyfile(self.index_path, legacy / "index.json")
        self.index_path.unlink()
        with self.assertRaises(FileNotFoundError):
            VERIFY.verify_repository(self.root)

    def test_unmigrated_run_catalog_is_rejected_before_scoring(self):
        self.index["hosted_development_runs"][0]["exported_run_path"] = "results/runs/v44"
        self.index_path.write_text(json.dumps(self.index), encoding="utf-8")
        with self.assertRaisesRegex(VERIFY.VerificationError, "must use data/results/runs"):
            VERIFY.verify_repository(self.root)

    def test_unmigrated_frozen_reference_catalog_is_rejected(self):
        self.index["exported_frozen_reference_path"] = "references/frozen_reference"
        self.index_path.write_text(json.dumps(self.index), encoding="utf-8")
        with self.assertRaisesRegex(VERIFY.VerificationError, "must use data/references"):
            VERIFY.verify_repository(self.root)

    def test_raw_report_tamper_stops_before_summary_generation(self):
        report = self.root / "data/results/runs/v49/run/report.json"
        report.write_bytes(report.read_bytes() + b"\n")
        with contextlib.redirect_stderr(io.StringIO()) as error:
            result = VERIFY.main(["--root", str(self.root), "--write-summary"])
        self.assertEqual(result, 1)
        self.assertIn("SHA-256 mismatch", error.getvalue())
        self.assertFalse((self.root / "data/results/summary.json").exists())

    def test_historical_code_tamper_is_detected(self):
        source = next((self.root / "archive/code/v46/evorationale").rglob("*.py"))
        source.write_bytes(source.read_bytes() + b"\n# tampered fixture\n")
        with self.assertRaisesRegex(VERIFY.VerificationError, "Historical code tree differs"):
            VERIFY.verify_repository(self.root)

    def test_different_csv_verdict_is_detected_by_independent_rescoring(self):
        run = self.index["hosted_development_runs"][-2]
        scorer = VERIFY.load_scorer(self.root, self.index)
        gold, _ = VERIFY.check_frozen_reference(self.root, self.index)
        report = VERIFY.read_json(self.root / run["exported_report_path"])
        metrics = VERIFY.read_json(self.root / run["exported_metrics_path"])
        errors = self.root / "data/results/runs/v49/score/link_errors.csv"
        contents = errors.read_text(encoding="utf-8-sig")
        self.assertIn(",TP,", contents)
        errors.write_text(contents.replace(",TP,", ",FP,", 1), encoding="utf-8", newline="")
        with self.assertRaisesRegex(VERIFY.VerificationError, "CSV rows differ"):
            VERIFY.compare_rescoring(scorer, gold, report, metrics, errors, run["label"])

    def test_zip_payload_cannot_be_replaced_by_updating_just_container_digest(self):
        run = self.index["hosted_development_runs"][0]
        archive = self.root / run["exported_raw_zip_path"]
        with zipfile.ZipFile(archive) as source:
            members = [(item.filename, source.read(item)) for item in source.infolist()]
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as destination:
            for name, content in members:
                destination.writestr(name, content + b" " if name == "report.json" else content)
        run["raw_upload_zip_sha256"] = VERIFY.digest(archive)
        self.index_path.write_text(json.dumps(self.index), encoding="utf-8")
        with self.assertRaisesRegex(VERIFY.VerificationError, "ZIP and exported member set differ"):
            VERIFY.verify_repository(self.root)

    def test_catalog_path_escape_is_rejected(self):
        self.index["hosted_development_runs"][0]["original_diagnostic_members"][0]["exported_path"] = "../outside.json"
        self.index_path.write_text(json.dumps(self.index), encoding="utf-8")
        with self.assertRaisesRegex(VERIFY.VerificationError, "Unsafe relative member path"):
            VERIFY.verify_repository(self.root)


if __name__ == "__main__":
    unittest.main()
