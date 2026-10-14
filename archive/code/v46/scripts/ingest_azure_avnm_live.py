"""Bounded read-only GitHub capture for one EvoRationale AVNM pilot.

Records *present-day* captured artifact versions; it NEVER backdates mutable
GitHub issue/PR/comment bodies to their creation dates. Original REST JSON
is archived locally with hashes for inspection. Do not use as historical replay.

Usage: python scripts/ingest_azure_avnm_live.py --decision <approved S0.json> --output data/live_avnm
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from evorationale.model import normalize_artifact, normalize_history, parse_timestamp, iso, validate_state

API = "https://api.github.com"
DEFAULT_REPO = "Azure/Enterprise-Scale"
DEFAULT_QUERIES = ("AVNM", '"Virtual Network Manager"')


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def save_json(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json(value)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def api_get(path: str, token: str | None = None) -> object:
    if not path.startswith("/") or ".." in path or path.startswith("//"):
        raise ValueError("Only official GitHub REST relative paths are allowed")
    req = Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "EvoRationale-AVNM-pilot/1.0",
        **({"Authorization": "Bearer " + token} if token else {}),
    })
    try:
        with urlopen(req, timeout=40) as resp:
            return json.load(resp)
    except HTTPError as exc:
        if exc.code in {403, 429}:
            raise RuntimeError("GitHub API rate limit or access denied. Wait for reset or configure a read-only GITHUB_TOKEN.") from exc
        raise RuntimeError(f"GitHub API HTTP {exc.code} at {path.split('?')[0]}") from exc
    except URLError as exc:
        raise RuntimeError("Could not contact public GitHub API; check network or proxy") from exc


def cutoff_safe_text(value: str | None, limit: int) -> tuple[str, bool, int]:
    value = (value or "").replace("\r\n", "\n")
    return value[:limit], len(value) > limit, len(value)


def build_record(*, repo: str, kind: str, identifier: str, title: str, body: str,
                 event_at: str, captured_at: str, url: str, meta: dict) -> dict:
    # FIRST AUDITABLE refers to this downloaded representation, not GitHub event creation.
    return normalize_artifact({
        "repository": repo,
        "artifact_id": f"github-{kind}-{identifier}",
        "source_type": kind,
        "title": title,
        "content": body,
        "timestamp": event_at,
        "first_auditable_at": captured_at,
        "source_location": url,
        "tags": ["AVNM", "live_capture"],
        "metadata": {**meta, "captured_at": captured_at,
                     "historical_replay_safe": False,
                     "immutable_source_object": kind == "commit"},
    })


def ingest(*, decision: dict, out: Path, repo: str = DEFAULT_REPO,
           max_prs: int = 8, max_comments_per_pr: int = 3,
           max_commits_per_pr: int = 3, max_content_chars: int = 3600,
           requester=api_get, now=None, token=None) -> dict:
    if min(max_prs, max_comments_per_pr, max_commits_per_pr, max_content_chars) < 1:
        raise ValueError("Positive limits required")
    state = validate_state(decision)
    if state["repository"] != repo:
        raise ValueError("Approved decision's repository must match the chosen GitHub repository")
    if state["human_approved"] is not True:
        raise ValueError("A human-approved S0 is required")
    if repo != DEFAULT_REPO:
        raise ValueError("This first bounded pilot is intentionally restricted to Azure/Enterprise-Scale")
    accepted_at = parse_timestamp(state["accepted_at"])
    capture_started = now() if now else datetime.now(timezone.utc)
    if capture_started.tzinfo is None:
        raise ValueError("Clock must include timezone")
    capture_started = capture_started.astimezone(timezone.utc)
    cap = iso(capture_started.isoformat())
    def audit_now() -> str:
        instant = now() if now else datetime.now(timezone.utc)
        if instant.tzinfo is None:
            raise ValueError("Audit clock must include timezone")
        return iso(instant.astimezone(timezone.utc).isoformat())
    selected: dict[int, dict] = {}
    inventory = []
    raw = {}
    fetch_calls = 0

    def fetch(path: str, key: str):
        nonlocal fetch_calls
        result = requester(path, token)
        fetch_calls += 1
        raw[key] = result
        return result

    for index, term in enumerate(DEFAULT_QUERIES):
        query = f"repo:{repo} is:pr {term}"
        path = "/search/issues?" + urlencode({"q": query, "per_page": 100, "page": 1})
        result = fetch(path, f"search-{index}")
        if not isinstance(result, dict) or not isinstance(result.get("items"), list):
            raise ValueError("Invalid GitHub search response")
        if result.get("total_count", 0) > len(result["items"]):
            inventory.append({"query": query, "warning": "SEARCH_PAGE_LIMIT_INCOMPLETE",
                              "total_count": result.get("total_count")})
        else:
            inventory.append({"query": query, "total_count": result.get("total_count", 0)})
        for row in result["items"]:
            num = row.get("number")
            if not isinstance(num, int) or not row.get("pull_request"):
                continue
            # Exclude original accepted decision anchor and PRs first opened before acceptance.
            created = row.get("created_at")
            if not created or parse_timestamp(created) <= accepted_at:
                continue
            selected[num] = row
    if not selected:
        raise RuntimeError("No post-acceptance candidate PRs were found; do not invent evidence")
    # Deterministic all-matching candidate ranking; not manually choosing favorable examples.
    candidates = sorted(selected.values(), key=lambda x:(x["created_at"],x["number"]))
    if len(candidates) > max_prs:
        inventory.append({"warning": "PR_CANDIDATES_TRUNCATED", "found": len(candidates), "kept": max_prs})
    candidates = candidates[:max_prs]
    records = []
    selected_numbers = []
    root = "/repos/Azure/Enterprise-Scale"
    for p in candidates:
        n = p["number"]
        full = fetch(f"{root}/pulls/{n}", f"pull-{n}")
        if not isinstance(full, dict) or full.get("number") != n:
            raise ValueError(f"Inconsistent PR response for {n}")
        if not full.get("created_at") or parse_timestamp(full["created_at"]) <= accepted_at:
            continue
        url = full.get("html_url")
        if not isinstance(url, str) or not url.startswith("https://github.com/Azure/Enterprise-Scale/pull/"):
            raise ValueError("Unexpected source URL; refuse to ingest")
        selected_numbers.append(n)
        body, truncated, original_size = cutoff_safe_text(full.get("body"), max_content_chars)
        records.append(build_record(repo=repo, kind="pull_request", identifier=str(n),
            title=full.get("title") or f"PR #{n}", body=body,
            event_at=full["created_at"], captured_at=audit_now(), url=url,
            meta={"github_number": n, "github_updated_at": full.get("updated_at"),
                  "github_merged_at": full.get("merged_at"),
                  "source_content_length": original_size, "excerpt_truncated": truncated,
                  "source_kind": "CURRENT_PR_BODY_SNAPSHOT"}))
        # Capture review and conversation comments. Mutable bodies are today-only versions.
        comments = []
        for family in ("issues", "pulls"):
            group = fetch(f"{root}/{family}/{n}/comments?per_page=100&page=1", f"comments-{family}-{n}")
            if not isinstance(group, list):
                raise ValueError("Unexpected GitHub comment response")
            if len(group) == 100:
                inventory.append({"warning":"COMMENTS_PAGINATION_INCOMPLETE", "family":family,"pr":n})
            for c in group:
                if c.get("created_at") and parse_timestamp(c["created_at"]) > accepted_at:
                    comments.append((family,c))
        comments.sort(key=lambda x:(x[1]["created_at"], x[1].get("id",0)))
        if len(comments)>max_comments_per_pr:
            inventory.append({"warning":"COMMENTS_SAMPLED", "pr":n,"found":len(comments),"kept":max_comments_per_pr})
        for family,c in comments[:max_comments_per_pr]:
            body, truncated, original_size = cutoff_safe_text(c.get("body"), max_content_chars)
            if not body.strip() or not c.get("html_url"):
                continue
            records.append(build_record(repo=repo, kind="review_comment" if family=="pulls" else "issue_comment",
                identifier=str(c["id"]), title=f"Comment on PR #{n}", body=body,
                event_at=c["created_at"], captured_at=audit_now(), url=c["html_url"],
                meta={"parent_pr": n,"github_updated_at":c.get("updated_at"),
                      "source_content_length":original_size,"excerpt_truncated":truncated,
                      "source_kind":"CURRENT_COMMENT_BODY_SNAPSHOT"}))
        # Commit SHAs identify immutable objects; record the current audit/capture time anyway.
        commit_list = fetch(f"{root}/pulls/{n}/commits?per_page=100&page=1", f"commit-list-{n}")
        if not isinstance(commit_list, list):
            raise ValueError("Invalid PR commit list")
        if len(commit_list) == 100:
            inventory.append({"warning":"COMMITS_PAGINATION_INCOMPLETE","pr":n})
        commits=[]
        for c in commit_list:
            commit_time = ((c.get("commit") or {}).get("committer") or {}).get("date")
            if c.get("sha") and commit_time and parse_timestamp(commit_time)>accepted_at:
                commits.append((commit_time,c["sha"]))
        commits.sort()
        if len(commits)>max_commits_per_pr:
            inventory.append({"warning":"COMMITS_SAMPLED", "pr":n,"found":len(commits),"kept":max_commits_per_pr})
        for _,sha in commits[-max_commits_per_pr:]:
            obj = fetch(f"{root}/commits/{sha}", f"commit-{sha}")
            if not isinstance(obj, dict) or obj.get("sha") != sha:
                raise ValueError("Commit SHA inconsistent with requested object")
            cm = obj.get("commit") or {}
            event = ((cm.get("committer") or {}).get("date") or (cm.get("author") or {}).get("date"))
            if not event or parse_timestamp(event) <= accepted_at:
                continue
            changed = [f"{f.get('status','')} {f.get('filename','')}" for f in obj.get("files", [])]
            content, truncated, original_size = cutoff_safe_text((cm.get("message") or "") +
                    "\nChanged files (GitHub commit metadata):\n" + "\n".join(changed), max_content_chars)
            records.append(build_record(repo=repo,kind="commit",identifier=sha,
                title=(cm.get("message") or "Commit").splitlines()[0], body=content,
                event_at=event,captured_at=audit_now(),
                url=obj.get("html_url") or f"https://github.com/Azure/Enterprise-Scale/commit/{sha}",
                meta={"sha":sha,"parent_pr":n,"source_kind":"IMMUTABLE_GIT_OBJECT_CURRENT_CAPTURE",
                      "source_content_length":original_size,"excerpt_truncated":truncated}))

    snapshot_ended = now() if now else datetime.now(timezone.utc)
    if snapshot_ended.tzinfo is None:
        raise ValueError("Clock must include timezone")
    # Cutoff after ingestion; do not pretend the snapshot existed at the PR's created_at.
    cutoff = iso((snapshot_ended.astimezone(timezone.utc)+timedelta(seconds=2)).isoformat())
    if parse_timestamp(cap) >= parse_timestamp(cutoff):
        raise ValueError("Invalid capture/cutoff timing")
    history = normalize_history(records)
    if not history:
        raise RuntimeError("No eligible GitHub records were collected")
    new_state = deepcopy(state)
    new_state["cutoff_at"] = cutoff
    new_state["episode_id"] = state["episode_id"] + "-live-github-pilot"
    new_state["research_label"] = "LIVE_PUBLIC_SNAPSHOT_PILOT_NOT_GOLD"
    new_state["snapshot_note"] = "Current captured source bodies cannot be used for historical cutoff replay"
    new_state = validate_state(new_state)
    if any(not accepted_at < parse_timestamp(a["first_auditable_at"]) <= parse_timestamp(cutoff) for a in history):
        raise ValueError("Encountered ineligible artifact timestamp")

    out.mkdir(parents=True,exist_ok=True)
    for k,v in raw.items():
        save_json(out/"raw"/(k+".json"),v)
    state_digest = save_json(out/"decision_state_LIVE.json",new_state)
    history_text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True)+"\n" for row in history)
    (out/"history_LIVE.jsonl").write_text(history_text, encoding="utf-8")
    sources = [{"artifact_id":a["artifact_id"],"source_location":a["source_location"],
                "first_auditable_at":a["first_auditable_at"],
                "original_timestamp":a["timestamp"],
                "content_sha256":a["content_sha256"],
                "excerpt_truncated":a["metadata"].get("excerpt_truncated")}
               for a in history]
    manifest={"source":"GitHub public REST API","repository":repo,
              "capture_started_at":cap,"cutoff_at":cutoff,
              "accepted_at":state["accepted_at"],"selected_pr_numbers":selected_numbers,
              "queries":list(DEFAULT_QUERIES),"query_and_sampling_warnings":inventory,
              "raw_api_calls":fetch_calls,
              "artifact_count":len(history),"artifact_types":{t:sum(a["source_type"]==t for a in history)
                  for t in sorted(set(a["source_type"] for a in history))},
              "decision_sha256":state_digest,
              "history_sha256":hashlib.sha256(history_text.encode("utf-8")).hexdigest(),
              "source_artifacts":sources,
              "disclosure":"LIVE CAPTURE OF CURRENT PUBLIC GITHUB RECORDS, NOT HISTORICAL REPLAY OR SANER STUDY RESULTS",
              "completeness":"BOUNDED SELECTIVE SEARCH. Not exhaustive history or independently adjudicated ground truth.",
              "human_review":"REQUIRED BEFORE TREATING OUTCOME AS SCIENTIFIC RESULT"}
    save_json(out/"github_capture_manifest.json",manifest)
    print(json.dumps({"status":"CAPTURED", "artifact_count":len(history),
          "pull_requests":selected_numbers,"github_api_calls":fetch_calls,
          "output":str(out),"cutoff_at":cutoff},indent=2,ensure_ascii=False))
    return manifest


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision",type=Path,required=True)
    parser.add_argument("--output",type=Path,default=Path("data/live_avnm"))
    parser.add_argument("--max-prs",type=int,default=6)
    parser.add_argument("--max-comments-per-pr",type=int,default=3)
    parser.add_argument("--max-commits-per-pr",type=int,default=3)
    parser.add_argument("--max-content-chars",type=int,default=3600)
    args=parser.parse_args()
    try:
        decision=json.loads(args.decision.read_text(encoding="utf-8"))
        ingest(decision=decision,out=args.output,max_prs=args.max_prs,
              max_comments_per_pr=args.max_comments_per_pr,
              max_commits_per_pr=args.max_commits_per_pr,
              max_content_chars=args.max_content_chars,token=os.getenv("GITHUB_TOKEN"))
    except (ValueError,RuntimeError,HTTPError,URLError) as exc:
        print("ERROR: "+str(exc),file=sys.stderr)
        raise SystemExit(1) from exc

if __name__ == "__main__":
    main()
