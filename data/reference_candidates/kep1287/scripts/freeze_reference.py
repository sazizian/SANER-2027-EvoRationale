#!/usr/bin/env python3
"""Record confirmed human consensus; this does not validate scientific truth."""
from __future__ import annotations
import argparse,csv,hashlib,json,shutil
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]
FIELDS=("accepts_exact_18_atomic_s0_text","accepts_23_commit_screening_with_abstentions",
"accepts_4_event_relations_and_temporal_basis","accepts_30_hunk_relation_maps","confirms_d7_commit_maps_to_I1")
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--confirmations",type=Path,required=True,help="Reviewer-confirmed CSV with archival links")
    p.add_argument("--output",type=Path,required=True,help="New empty folder for the frozen reference")
    args=p.parse_args()
    with args.confirmations.open(encoding="utf-8-sig",newline="") as stream:rows=list(csv.DictReader(stream))
    if {r.get("reviewer_id") for r in rows}!={"Reviewer A","Reviewer B"} or len(rows)!=2:
        raise ValueError("Exactly Reviewer A and Reviewer B confirmation records are required")
    for row in rows:
        for field in FIELDS:
            if str(row.get(field,"")).strip().upper()!="YES":
                raise ValueError(f"{row['reviewer_id']}: {field} is not confirmed")
        for field in ("confirmation_date_utc","confirmation_method","external_record_reference","reviewer_name_or_identifier"):
            if not str(row.get(field,"")).strip():raise ValueError(f"Missing {field} for {row['reviewer_id']}")
        if not str(row["confirmation_date_utc"]).endswith("Z"):
            raise ValueError("confirmation_date_utc must contain explicit UTC Z timestamp")
        datetime.fromisoformat(str(row["confirmation_date_utc"]).replace("Z","+00:00"))
    if args.output.exists():raise FileExistsError(f"Refusing to overwrite existing output: {args.output}")
    args.output.mkdir(parents=True)
    (args.output/"reference").mkdir()
    files=["S0_ATOMIC_CANDIDATE.csv","COMMIT_SCREENING_CANDIDATE.csv",
           "EVENT_RELATIONS_CANDIDATE.csv","HUNK_RELATIONS_CANDIDATE.csv"]
    for name in files:
        shutil.copy2(ROOT/"reference_private"/name,args.output/"reference"/name)
    st=json.loads((ROOT/"benchmark_inputs/S0_ATOMIC_CANDIDATE_UNAPPROVED.json").read_text(encoding="utf-8"))
    st["human_approved"]=True
    st["builder_status"]="TWO_DOCUMENTED_REVIEWER_CONFIRMATIONS_RECORDED"
    st["research_label"]="TWO_REVIEWER_CONSENSUS_RECORDED_NOT_HISTORICAL_REPLAY_CERTIFIED"
    st["signoff_sha256"]=digest(args.confirmations)
    out_state=args.output/"S0_ATOMIC_REVIEWER_CONFIRMED.json"
    out_state.write_text(json.dumps(st,sort_keys=True,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
    m={"status":"DOCUMENTED_SIGNOFF_RECORDED_NOT_INDEPENDENTLY_AUTHENTICATED",
       "reviewer_ids":sorted([r["reviewer_id"] for r in rows]),
       "confirmation_file_sha256":digest(args.confirmations),
       "reference_sha256":{name:digest(args.output/"reference"/name) for name in files},
       "s0_sha256":digest(out_state),
       "historical_replay_certified":False,
       "gold_decision_outcomes_available":False,
       "note":"The tool checks declarations and source integrity, not human identity, replay availability, or label validity."}
    (args.output/"FREEZE_MANIFEST.json").write_text(json.dumps(m,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    shutil.copy2(args.confirmations,args.output/"REVIEWER_CONFIRMATIONS.csv")
    print(json.dumps({"status":m["status"],"output":str(args.output),"s0_sha256":m["s0_sha256"]},indent=2))
if __name__=="__main__":main()
