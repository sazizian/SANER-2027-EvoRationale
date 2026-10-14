"""Offline tests for KEP-1287 baseline capture and auditable metadata."""
from __future__ import annotations
import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "capture_kep1287.py"
spec = importlib.util.spec_from_file_location("kep1287_capture", SCRIPT)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class CaptureTests(unittest.TestCase):
    def test_git_blob_sha_matches_github_object(self):
        content = b"Example byte sequence.\n"
        self.assertEqual(len(collector.git_blob_sha1(content)), 40)
        self.assertNotEqual(collector.git_blob_sha1(content), collector.sha256(content))
        self.assertNotEqual(collector.git_blob_sha1(content), collector.git_blob_sha1(content + b" "))

    def test_hist_text_parser_checks_required_headings(self):
        good = "\n".join(["## Summary", "## Motivation", "### Goals", "### Non-Goals", "## Proposal", "## Alternatives"])
        collector.validate_headings(good)
        with self.assertRaisesRegex(RuntimeError, "missing expected heading"):
            collector.validate_headings("## Summary\n## Motivation\n")

    def test_blob_declared_and_computed_sha_must_match(self):
        data = b"short test readme"
        sha = collector.git_blob_sha1(data)
        fake = lambda url: {"content": base64.b64encode(data).decode(), "encoding": "base64", "sha": sha}
        self.assertEqual(collector.contents_at_commit(fake, collector.README_PATH, sha), data)
        with self.assertRaisesRegex(RuntimeError, "Git blob mismatch"):
            collector.contents_at_commit(fake, collector.README_PATH, "0" * 40)

    def test_history_filters_baseline_and_end_window(self):
        ts = ["2023-10-26T15:17:39Z", "2024-06-07T07:07:54Z", "2024-10-11T00:00:00Z"]
        rows = [{"sha": f"{x+1:040x}", "commit": {"committer": {"date": d}, "message": f"event {x}"},
                 "html_url": "https://github.com/kubernetes/enhancements/commit/" + f"{x+1:040x}"}
                for x, d in enumerate(ts)]
        captured = collector.commit_rows(lambda url: rows, collector.CUTOFF_AT)
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0]["committer_date"], ts[1])

    def test_capture_is_transactional_and_refuses_overwrite(self):
        readme = "\n".join(["## Summary", "## Motivation", "### Goals", "### Non-Goals", "## Proposal", "## Alternatives"])
        readme_bytes = readme.encode()
        yaml_bytes = b"status: implementable\nstage: \"alpha\"\n"
        event_dates = ["2024-06-07T07:07:54Z", "2024-09-17T00:06:36Z", "2024-09-30T23:54:56Z", "2024-10-10T00:07:16Z"]
        shas = list(collector.CURATED_COMMITS)
        entries = [{"sha": s, "commit": {"committer": {"date": d}, "message": "test change"},
                    "html_url": f"https://github.com/kubernetes/enhancements/commit/{s}"}
                   for s, d in zip(shas, event_dates)]
        def fetch(url):
            if url.endswith(f"/commits/{collector.BASELINE_COMMIT}"):
                return {"sha": collector.BASELINE_COMMIT, "commit": {"committer": {"date": collector.BASELINE_AT}}}
            if "/contents/" in url:
                data = readme_bytes if "README.md" in url else yaml_bytes
                return {"sha": collector.git_blob_sha1(data), "encoding": "base64", "content": base64.b64encode(data).decode()}
            if "/commits?" in url:
                return entries
            for sha, date in zip(shas, event_dates):
                if url.endswith(f"/commits/{sha}"):
                    return {"sha": sha, "commit": {"committer": {"date": date}},
                            "files": [{"filename": collector.README_PATH, "status": "modified", "patch": "+test change"}]}
            raise AssertionError(f"Unexpected mocked endpoint: {url}")
        with tempfile.TemporaryDirectory() as tdir, \
             patch.object(collector, "BASELINE_README_BLOB", collector.git_blob_sha1(readme_bytes)), \
             patch.object(collector, "BASELINE_YAML_BLOB", collector.git_blob_sha1(yaml_bytes)):
            out = Path(tdir) / "output"
            info = collector.capture(fetch, out)
            self.assertEqual(info["timeline_commits"], 4)
            self.assertFalse(info["historical_replay_certified"])
            self.assertEqual((out / "baseline_README_2023.md").read_bytes(), readme_bytes)
            manifest = json.loads((out / "capture_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["baseline_readme_sha256"], collector.sha256(readme_bytes))
            self.assertFalse(manifest["baseline_approval_event_verified"])
            with self.assertRaises(FileExistsError):
                collector.capture(fetch, out)


if __name__ == "__main__":
    unittest.main()
