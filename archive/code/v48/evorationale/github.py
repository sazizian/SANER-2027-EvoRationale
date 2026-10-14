"""GitHub ingestion preserving version and first-auditable timestamps.

IMPORTANT: GitHub's current issue/PR body must never be passed off as the text
that existed at created_at. For mutable items, first_auditable_at is the
capture timestamp unless a signed historical archive provides an earlier version.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from typing import Any
from urllib.request import Request, urlopen
from urllib.parse import quote
from urllib.error import HTTPError

from .model import iso, normalize_artifact, normalize_history


def normalize_github_export(repo: str, payload: dict[str, list[dict[str, Any]]],
                            captured_at: str) -> list[dict[str, Any]]:
    """Convert an explicitly captured GitHub API export to versioned artifacts.

    Each item may contain `historical_versions` with independently attested timestamps,
    which must be validated before use. Default is a CURRENT snapshot, not history replay.
    """
    captured_at = iso(captured_at)
    types = {"issues": "issue", "pulls": "pull_request", "commits": "commit",
             "issue_comments": "issue_comment", "pull_comments": "pull_comment",
             "releases": "release", "incidents": "incident", "benchmarks": "benchmark",
             "tests": "test"}
    rows = []
    for group, source_type in types.items():
        for item in payload.get(group, []):
            if source_type == "issue" and "pull_request" in item:
                continue
            commit = item.get("commit") if source_type == "commit" else None
            if isinstance(commit, dict):
                title = (commit.get("message") or "commit").splitlines()[0]
                content = commit.get("message") or ""
                item_id = item.get("sha") or item.get("id")
                event_time = ((commit.get("committer") or {}).get("date") or
                              (commit.get("author") or {}).get("date"))
            else:
                title = item.get("title") or item.get("name") or source_type
                content = item.get("body") or item.get("content") or ""
                item_id = item.get("number") or item.get("id") or item.get("sha")
                event_time = (item.get("updated_at") or item.get("published_at") or
                              item.get("created_at") or captured_at)
            if item_id is None:
                raise ValueError(f"Missing GitHub identifier for {source_type}")
            if not item.get("html_url") and not item.get("source_location"):
                raise ValueError("GitHub artifact missing canonical URL")
            if iso(event_time) > captured_at:
                raise ValueError("GitHub event timestamp is after capture timestamp")
            row = {"repository": repo, "artifact_id": f"{source_type}-{item_id}",
                   "source_type": source_type, "title": title, "content": content,
                   "timestamp": event_time, "first_auditable_at": captured_at,
                   "source_location": item.get("html_url") or item.get("source_location"),
                   "tags": [x["name"] for x in item.get("labels", []) if isinstance(x, dict) and x.get("name")],
                   "metadata": {"captured_at": captured_at, "historical_replay_safe": False,
                                "immutable_snapshot": source_type == "commit"}}
            rows.append(normalize_artifact(row))
            # Historical versions are allowed ONLY with an independently sourced audit time.
            # Do not manufacture versions from the 'updated_at' field of a current item.
            for historical in item.get("historical_versions", []):
                if not historical.get("attested_first_auditable_at") or not historical.get("content"):
                    raise ValueError("Historical version requires attested_first_auditable_at and archived content")
                archived = {**row, "content": historical["content"],
                            "timestamp": historical["timestamp"],
                            "first_auditable_at": historical["attested_first_auditable_at"],
                            "version_id": historical["version_id"],
                            "metadata": {"historical_replay_safe": True,
                                         "attestation": historical.get("attestation", "external_manual_archive")}}
                rows.append(normalize_artifact(archived))
    return normalize_history(rows)


class GitHubClient:
    """Read-only GitHub REST snapshot loader. For historic studies supply audited exports."""
    def __init__(self, token: str | None = None, api_base: str = "https://api.github.com") -> None:
        if api_base != "https://api.github.com":
            raise ValueError("Only the official GitHub HTTPS API endpoint is supported")
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.root = api_base

    def _pages(self, path: str, max_pages: int = 20) -> list[dict[str, Any]]:
        results = []
        for page in range(1, max_pages + 1):
            req = Request(f"{self.root}{path}{'&' if '?' in path else '?'}per_page=100&page={page}",
                          headers={"Accept": "application/vnd.github+json", "User-Agent": "EvoRationale/2",
                                   **({"Authorization": "Bearer " + self.token} if self.token else {})})
            try:
                with urlopen(req, timeout=30) as response:
                    batch = json.load(response)
            except HTTPError as exc:
                raise RuntimeError(f"GitHub API returned HTTP {exc.code}") from exc
            if not isinstance(batch, list):
                raise ValueError("Expected a paginated GitHub list")
            results.extend(batch)
            if len(batch) < 100:
                break
        else:
            raise RuntimeError("GitHub page limit reached; do not silently truncate a snapshot")
        return results

    def capture(self, repo: str) -> list[dict[str, Any]]:
        parts = repo.split("/")
        if len(parts) != 2 or not all(parts):
            raise ValueError("GitHub repo must be owner/name")
        path = f"/repos/{quote(parts[0], safe='')}/{quote(parts[1], safe='')}"
        captured_at = datetime.now(timezone.utc).isoformat()
        payload = {"issues": self._pages(path + "/issues?state=all"),
                   "pulls": self._pages(path + "/pulls?state=all"),
                   "commits": self._pages(path + "/commits"),
                   "issue_comments": self._pages(path + "/issues/comments"),
                   "pull_comments": self._pages(path + "/pulls/comments"),
                   "releases": self._pages(path + "/releases")}
        return normalize_github_export(repo, payload, captured_at)
