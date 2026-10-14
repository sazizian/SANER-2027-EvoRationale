#!/usr/bin/env python3
"""Capture immutable KEP-1287 baseline files and a bounded post-baseline GitHub timeline.

Standard library only. All outputs are new research artifacts; existing EvoRationale
code, approved decision states, and prior datasets are never touched.

This script does not grant scientific ground-truth status or historical replay
certification. The pinned commit and blob hashes are independently checked.
"""
from __future__ import annotations

import argparse
import base64
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

REPO = "kubernetes/enhancements"
KEP_PATH = "keps/sig-node/1287-in-place-update-pod-resources"
README_PATH = f"{KEP_PATH}/README.md"
YAML_PATH = f"{KEP_PATH}/kep.yaml"
BASELINE_COMMIT = "5950905de89aab2be202d28b823701276cbefea0"
BASELINE_README_BLOB = "ce5124cf7975a7d4ce6a122b2cb4006b4bc0ea2d"
BASELINE_YAML_BLOB = "fd75bc9a121275a09debf7fd55304b483405bd36"
BASELINE_AT = "2023-10-26T15:17:39Z"
CUTOFF_AT = "2024-10-11T00:00:00Z"

# These are candidate changes for independent adjudication, never gold labels.
CURATED_COMMITS = {
    "68952e4476e47eb71321a2c7f92844e602d38d22": "Beta planning and lifecycle requirements",
    "079aa5fb9ab1a66f09f1d0c841025f7451474265": "Revisions after offline design discussions",
    "964260d9c2da8f75423771fffd9989077d4d92aa": "AllocatedResources moves outside core beta scope",
    "04de3dac4669f4b2f792c17488c680ce4b144679": "ResizePolicy mutability revision",
}


def timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()


def github_api_json(url: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "EvoRationale-KEP1287-Historical-Capture",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        if exc.code in (403, 429):
            raise RuntimeError("GitHub API rate limit or access restriction. Retry later, or set GITHUB_TOKEN locally; never include the token in shared research files.") from exc
        raise RuntimeError(f"GitHub API HTTP {exc.code} for {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"GitHub network request failed: {exc.reason}") from exc


def contents_at_commit(fetch, path: str, expected_blob_sha: str) -> bytes:
    url = f"https://api.github.com/repos/{REPO}/contents/{quote(path, safe='/')}?ref={BASELINE_COMMIT}"
    record = fetch(url)
    if not isinstance(record, dict):
        raise RuntimeError(f"Expected GitHub Contents object for {path}")
    if record.get("encoding") != "base64":
        raise RuntimeError(f"Unexpected GitHub Contents encoding for {path}")
    data = base64.b64decode(record["content"], validate=False)
    declared = record.get("sha", "")
    computed = git_blob_sha1(data)
    if declared != expected_blob_sha or computed != expected_blob_sha:
        raise RuntimeError(f"Immutable Git blob mismatch for {path}: expected {expected_blob_sha}, got {declared}/{computed}")
    return data


def commit_rows(fetch, until: str, max_pages: int = 10) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    params = {"path": README_PATH, "since": BASELINE_AT,
              "until": until, "per_page": 100}
    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/repos/{REPO}/commits?{urlencode({**params, 'page': page})}"
        found = fetch(url)
        if not isinstance(found, list):
            raise RuntimeError("Expected a list from the GitHub commit-history endpoint")
        for record in found:
            commit_sha = record.get("sha", "")
            if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
                raise RuntimeError("GitHub returned an invalid commit SHA")
            date = record.get("commit", {}).get("committer", {}).get("date", "")
            if not date:
                raise RuntimeError(f"Missing committer date for {commit_sha}")
            if not (timestamp(BASELINE_AT) < timestamp(date) < timestamp(until)):
                continue
            if commit_sha not in seen:
                seen.add(commit_sha)
                rows.append({"commit_sha": commit_sha, "committer_date": date,
                             "message": record.get("commit", {}).get("message", "").split("\n")[0],
                             "source_url": record.get("html_url") or f"https://github.com/{REPO}/commit/{commit_sha}"})
        if len(found) < 100:
            break
    else:
        raise RuntimeError("Commit history exceeded max_pages; refusing to label an incomplete timeline as complete")
    return sorted(rows, key=lambda x: (x["committer_date"], x["commit_sha"]))


def validate_headings(text: str) -> None:
    for heading in ("## Summary", "## Motivation", "### Goals", "### Non-Goals",
                    "## Proposal", "## Alternatives"):
        if heading not in text:
            raise RuntimeError(f"Pinned KEP README is missing expected heading: {heading}")


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], keys: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows([{k: row.get(k, "") for k in keys} for row in rows])


def capture(fetch, dest: Path) -> dict:
    dest = dest.expanduser().resolve()
    if dest.exists():
        raise FileExistsError(f"Output directory already exists: {dest}. Choose a new directory; existing captures are immutable.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="kep1287_stage_", dir=dest.parent))
    try:
        captured_at = now_iso()
        commit_url = f"https://api.github.com/repos/{REPO}/commits/{BASELINE_COMMIT}"
        c = fetch(commit_url)
        if not isinstance(c, dict) or c.get("sha") != BASELINE_COMMIT:
            raise RuntimeError("Pinned baseline commit SHA was not returned by GitHub")
        actual_date = c.get("commit", {}).get("committer", {}).get("date")
        if actual_date != BASELINE_AT:
            raise RuntimeError(f"Pinned baseline committer date changed: {actual_date}")
        readme = contents_at_commit(fetch, README_PATH, BASELINE_README_BLOB)
        yaml = contents_at_commit(fetch, YAML_PATH, BASELINE_YAML_BLOB)
        decoded = readme.decode("utf-8", "strict")
        validate_headings(decoded)
        text_yaml = yaml.decode("utf-8", "strict")
        if not re.search(r"^status:\s*implementable\s*$", text_yaml, flags=re.MULTILINE):
            raise RuntimeError("Baseline kep.yaml does not contain status: implementable")
        if not re.search(r"^stage:\s*['\"]?alpha", text_yaml, flags=re.MULTILINE):
            raise RuntimeError("Baseline kep.yaml does not contain stage: alpha")
        (stage / "baseline_README_2023.md").write_bytes(readme)
        (stage / "baseline_kep_2023.yaml").write_bytes(yaml)

        entries = commit_rows(fetch, CUTOFF_AT)
        row_by_sha = {row["commit_sha"]: row for row in entries}
        absent = sorted(set(CURATED_COMMITS) - row_by_sha.keys())
        if absent:
            raise RuntimeError(f"Curated commits missing from verified path history: {', '.join(absent)}")
        for sha, subject in CURATED_COMMITS.items():
            detail_url = f"https://api.github.com/repos/{REPO}/commits/{sha}"
            detail = fetch(detail_url)
            if not isinstance(detail, dict) or detail.get("sha") != sha:
                raise RuntimeError(f"Mismatch for curated commit {sha}")
            date = detail.get("commit", {}).get("committer", {}).get("date")
            if date != row_by_sha[sha]["committer_date"]:
                raise RuntimeError(f"Inconsistent commit dates for {sha}")
            changed = [f for f in detail.get("files", []) if f.get("filename") in (README_PATH, YAML_PATH)]
            if not any(x.get("filename") == README_PATH for x in changed):
                raise RuntimeError(f"Pinned commit lacks the required KEP README change: {sha}")
            payload = {
                "commit_sha": sha, "committer_date": date,
                "candidate_research_topic": subject,
                "source_url": f"https://github.com/{REPO}/commit/{sha}",
                "files": [{"path": x.get("filename"), "status": x.get("status"),
                           "patch_available": bool(x.get("patch")), "patch": x.get("patch")}
                          for x in changed],
                "annotation_status": "NOT_ADJUDICATED",
                "replay_certification": "NOT_CERTIFIED",
            }
            write_json(stage / "selected_commit_diffs" / f"{sha}.json", payload)
        write_csv(stage / "all_readme_commits_in_window.csv", entries,
                  ["commit_sha", "committer_date", "message", "source_url"])
        annotated = [{**row, "candidate_research_topic": CURATED_COMMITS[sha],
                      "reviewer_relation": "UNDECIDED", "rationale_relevance": "UNDECIDED"}
                     for sha, row in row_by_sha.items() if sha in CURATED_COMMITS]
        annotated.sort(key=lambda r: r["committer_date"])
        write_csv(stage / "selected_events_for_review.csv", annotated,
                  ["commit_sha", "committer_date", "message", "candidate_research_topic",
                   "source_url", "reviewer_relation", "rationale_relevance"])
        manifest = {
            "status": "CAPTURED_REQUIRES_HUMAN_ADJUDICATION",
            "repository": REPO,
            "source_path": README_PATH,
            "baseline_commit": BASELINE_COMMIT,
            "baseline_commit_time": BASELINE_AT,
            "baseline_approval_event_verified": False,
            "baseline_metadata_status": "implementable",
            "baseline_metadata_stage": "alpha",
            "baseline_readme_git_blob_sha1": BASELINE_README_BLOB,
            "baseline_kep_yaml_git_blob_sha1": BASELINE_YAML_BLOB,
            "baseline_readme_sha256": sha256(readme),
            "baseline_kep_yaml_sha256": sha256(yaml),
            "window_end_exclusive": CUTOFF_AT,
            "commit_rows_in_window": len(entries),
            "curated_commits_verified": list(CURATED_COMMITS),
            "captured_at": captured_at,
            "historical_replay_certified": False,
            "human_adjudicated_ground_truth": False,
            "source_kind": "Immutable git commit objects captured retrospectively",
            "research_warning": "The baseline commit is a reproducible 2023 revision, not proof of first acceptance. Commits and patches are candidate change evidence, not drift labels.",
        }
        write_json(stage / "capture_manifest.json", manifest)
        stage.rename(dest)
        return {"status": manifest["status"], "output": str(dest),
                "baseline_verified": True, "timeline_commits": len(entries),
                "curated_commit_diffs": len(CURATED_COMMITS),
                "historical_replay_certified": False}
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "captured")
    args = parser.parse_args()
    try:
        result = capture(github_api_json, args.output)
    except (RuntimeError, OSError, ValueError) as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc)}, ensure_ascii=True, indent=2), file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
