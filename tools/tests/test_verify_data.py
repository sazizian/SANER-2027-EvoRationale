"""Central resource inventory and canonical-input boundary checks; no API."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


SPEC = importlib.util.spec_from_file_location("export_data_verifier", Path(__file__).parents[1] / "verify_data.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class VerifyCentralData(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="central_data_verify_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        inputs = {
            VERIFY.INPUT_FILENAMES[0]: b'{"decision": "test fixture"}\n',
            VERIFY.INPUT_FILENAMES[1]: b"".join(
                (json.dumps({"artifact_id": f"fixture-{i}"}) + "\n").encode("utf-8") for i in range(53)),
        }
        self.entries = []
        original_members = []
        for filename, content in inputs.items():
            relative = f"{VERIFY.INPUT_DIRECTORY}/{filename}"
            self.put(relative, content)
            self.entries.append(self.entry(relative, "fixed_unlabeled_runtime_input", "CONFIRMED_RUN_INPUT"))
            preserved = f"data/results/runs/v49/inputs/{filename}"
            self.put(preserved, content)
            original_members.append({"member": f"inputs/{filename}", "exported_path": preserved,
                                     "sha256": hashlib.sha256(content).hexdigest()})
        self.workbook = self.root / "data/excel/resource.xlsx"
        self.workbook.parent.mkdir(parents=True)
        with zipfile.ZipFile(self.workbook, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("xl/workbook.xml", "<workbook/>")
        self.entries.append(self.entry("data/excel/resource.xlsx", "supplied_workbook", "ORIGINAL_RESOURCE"))
        results = {"hosted_development_runs": [{"label": "v4.9", "original_diagnostic_members": original_members}]}
        self.put("data/results/index.json", json.dumps(results).encode("utf-8"))
        self.write_inventory()

    def put(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def entry(self, relative, role, status):
        path = self.root / relative
        return {"path": relative, "source_path": f"original_resource/{path.name}",
                "sha256": VERIFY.file_digest(path), "size_bytes": path.stat().st_size,
                "role": role, "status": status, "byte_preserved": True}

    def write_inventory(self):
        catalog = {"catalog_kind": VERIFY.CATALOG_KIND, "source_files_are_byte_preserved": True,
                   "reference_labels_are_post_run_scoring_only": True, "entries": self.entries}
        self.put("data/RESOURCE_INDEX.json", json.dumps(catalog).encode("utf-8"))
        with (self.root / "data/RESOURCE_INDEX.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=VERIFY.CATALOG_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(self.entries)

    def test_verified_resources_are_read_only_and_keep_53_original_inputs(self):
        before = {p.relative_to(self.root): VERIFY.file_digest(p) for p in self.root.rglob("*") if p.is_file()}
        audit = VERIFY.verify_data(self.root)
        after = {p.relative_to(self.root): VERIFY.file_digest(p) for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(audit["resource_files_verified"], 3)
        self.assertEqual(audit["canonical_history_artifact_count"], 53)
        self.assertEqual(audit["excel_workbook_zip_integrity_checks"], 1)
        self.assertEqual(audit["provider_requests_made"], 0)

    def test_resource_byte_tamper_is_detected(self):
        content = self.workbook.read_bytes()
        self.workbook.write_bytes(content[:-1] + bytes([content[-1] ^ 1]))
        with self.assertRaisesRegex(ValueError, "Data resource SHA-256 differs"):
            VERIFY.verify_data(self.root)

    def test_csv_cannot_silently_disagree_with_json_inventory(self):
        path = self.root / "data/RESOURCE_INDEX.csv"
        path.write_text(path.read_text().replace("supplied_workbook", "confirmed_input", 1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Resource CSV rows differ"):
            VERIFY.verify_data(self.root)

    def test_resource_path_cannot_escape_data(self):
        self.entries[-1]["path"] = "data/../outside.xlsx"
        self.write_inventory()
        with self.assertRaisesRegex(ValueError, "Unsafe data resource path"):
            VERIFY.verify_data(self.root)

    def test_relabeling_modified_model_input_cannot_replace_pinned_v49_input(self):
        item = self.entries[0]
        path = self.root / item["path"]
        path.write_bytes(path.read_bytes() + b" ")
        item["sha256"] = VERIFY.file_digest(path)
        item["size_bytes"] = path.stat().st_size
        self.write_inventory()
        with self.assertRaisesRegex(ValueError, "Canonical model input differs from preserved v4.9 input"):
            VERIFY.verify_data(self.root)

    def test_hash_matched_zip_still_needs_excel_workbook_structure(self):
        with zipfile.ZipFile(self.workbook, "w") as archive:
            archive.writestr("plain-text.txt", "not an Excel workbook")
        self.entries[-1]["sha256"] = VERIFY.file_digest(self.workbook)
        self.entries[-1]["size_bytes"] = self.workbook.stat().st_size
        self.write_inventory()
        with self.assertRaisesRegex(ValueError, "Missing Excel workbook structure"):
            VERIFY.verify_data(self.root)


if __name__ == "__main__":
    unittest.main()
