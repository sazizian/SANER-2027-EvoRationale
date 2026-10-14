#!/usr/bin/env python3
"""Read-only integrity and readiness checks for the KEP-1287 candidate package."""
from __future__ import annotations
import csv, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read_csv(path):
    with path.open(newline="",encoding="utf-8-sig") as handle:return list(csv.DictReader(handle))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
    root=ROOT
    baseline=json.loads((root/"sources/capture_manifest.json").read_text(encoding="utf-8"))
    if (root/"SHA256SUMS.json").exists():
        checksum=json.loads((root/"SHA256SUMS.json").read_text(encoding="utf-8"))
        for relative, expected in checksum["files"].items():
            full=root/relative
            assert full.is_file() and sha(full)==expected, f"File checksum mismatch: {relative}"
    assert sha(root/"sources/baseline_README_2023.md")==baseline["baseline_readme_sha256"],"README hash mismatch"
    assert sha(root/"sources/baseline_kep_2023.yaml")==baseline["baseline_kep_yaml_sha256"],"YAML hash mismatch"
    s0=json.loads((root/"benchmark_inputs/S0_ATOMIC_CANDIDATE_UNAPPROVED.json").read_text(encoding="utf-8"))
    atomic=read_csv(root/"reference_private/S0_ATOMIC_CANDIDATE.csv")
    screening=read_csv(root/"reference_private/COMMIT_SCREENING_CANDIDATE.csv")
    events=read_csv(root/"reference_private/EVENT_RELATIONS_CANDIDATE.csv")
    hunks=read_csv(root/"reference_private/HUNK_RELATIONS_CANDIDATE.csv")
    hist=[json.loads(x) for x in (root/"benchmark_inputs/POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(atomic)==18 and len(screening)==23 and len(events)==4 and len(hunks)==30 and len(hist)==53
    assert s0["human_approved"] is False,"Do not ship falsely approved S0"
    elemids={r["element_id"] for r in atomic}
    assert len(elemids)==18
    for group in ("goals","requirements","assumptions","original_evidence","quality_attributes","constraints_dependencies","implementation_scope"):
        assert all(x["id"] in elemids for x in s0[group])
    assert len({a["artifact_id"] for a in hist})==53
    assert all(a.get("historical_replay_safe") is False and a.get("retrospective_capture") is True for a in hist)
    assert all("relation_candidate" not in a and "screening_label" not in a for a in hist),"Gold leakage in agent inputs"
    assert all(x["temporal_basis"] if "temporal_basis" in x else True for x in events)
    by_id={x["artifact_id"]:x for x in hist}
    for row in hunks:
        assert row["hunk_id"] in by_id
        assert hashlib.sha256(by_id[row["hunk_id"]]["content"].encode("utf-8")).hexdigest()==row["hunk_sha256"],row["hunk_id"]
        assert all(t in elemids for t in row["related_atomic_s0_ids"].split(";") if t),row["hunk_id"]
    assert any(r["commit_sha"].startswith("d7b996") and "I1" in r["s0_element_ids"].split(";") for r in screening)
    assert any(r["temporal_basis"]=="INTERIM_2024" for r in events)
    return {"status":"PASS_CANDIDATE_NOT_FROZEN_GOLD",
            "s0_atomic_elements":18,"commits_screened":23,"selected_events":4,
            "indexed_hunks":30,"unlabeled_evidence_artifacts":53,
            "source_sha256_verified":True,"reviewer_signatures_verified":False,
            "historical_replay_certified":False}
if __name__=="__main__":
    try:print(json.dumps(check(),indent=2))
    except Exception as e:
        print(json.dumps({"status":"ERROR","reason":str(e)},indent=2))
        raise
