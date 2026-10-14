#!/usr/bin/env python3
"""Provisional hunk relation scoring. NOT publication metrics."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POSITIVE={"SUPPORTS":"supports","WEAKENS":"weakens","CONTRADICTS":"contradicts","SUPERSEDES":"supersedes"}
def score(report,scope="baseline"):
    with (ROOT/"reference_private/HUNK_RELATIONS_CANDIDATE.csv").open(encoding="utf-8",newline="") as stream:
        rows=list(csv.DictReader(stream))
    if scope=="baseline":
        rows=[r for r in rows if r["temporal_basis_inherited_from_event"]!="INTERIM_2024"]
    universe={r["hunk_id"] for r in rows}
    gold={(r["hunk_id"],eid,POSITIVE[r["relation_candidate"]])
          for r in rows if r["relation_candidate"] in POSITIVE
          for eid in r["related_atomic_s0_ids"].split(";") if eid}
    predictions=report.get("verified_evidence",[])
    pred={(str(a.get("artifact_id") or ""),str(a.get("decision_element_id") or ""),str(a.get("relation") or "").lower())
          for a in predictions if str(a.get("artifact_id") or "") in universe and a.get("relation") in POSITIVE.values()}
    tp,fp,fn=len(pred&gold),len(pred-gold),len(gold-pred)
    precision=tp/(tp+fp) if tp+fp else 0.0
    recall=tp/(tp+fn) if tp+fn else 0.0
    return {"status":"EXPLORATORY_PI_ATTESTED_CANDIDATE_NOT_PUBLISHED_GOLD",
      "scope":scope,"evaluated_hunks":len(universe),"positive_reference_triples":len(gold),
      "predicted_triples_in_scope":len(pred),
      "tp":tp,"fp":fp,"fn":fn,
      "precision":precision,"recall":recall,
      "f1":(2*precision*recall/(precision+recall)) if precision+recall else 0.0,
      "outcome_accuracy":None,"historical_replay_certified":False,
      "notes":"Single repository, reviewer signoff absent from source workbook; not a publication-quality metric."}
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--scope",choices=["baseline","all"],default="baseline")
    p.add_argument("--allow-provisional",action="store_true")
    args=p.parse_args()
    if not args.allow_provisional:
        p.error("This reference is provisional. Pass --allow-provisional only for development diagnostics.")
    obj=json.loads(args.report.read_text(encoding="utf-8"))
    print(json.dumps(score(obj,scope=args.scope),indent=2))
