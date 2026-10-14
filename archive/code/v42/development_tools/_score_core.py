#!/usr/bin/env python3
"""Score an already completed, isolated EvoRationale run against a frozen reference.

Exact-match link triples, not a gold-label architectural decision evaluation.
No reviewer label is accessed until AFTER the agent run exists.
"""
from __future__ import annotations
import argparse, hashlib, json, csv, sys
from pathlib import Path
from collections import Counter

HUNK_FILE = 'HUNK_RELATIONS_CANDIDATE.csv'
POSITIVE = {'SUPPORTS': 'supports', 'WEAKENS':'weakens', 'CONTRADICTS':'contradicts',
            'SUPERSEDES':'supersedes'}
KNOWN = set(POSITIVE) | {'UNRELATED','IMPLEMENTATION_ONLY'}
EVAL_SCOPES = ('baseline','all')

def digest(file):
    h=hashlib.sha256()
    with Path(file).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def code_tree_hash(root):
    source=Path(root).resolve()
    paths=sorted((source/'evorationale').rglob('*.py'))
    if not paths:raise ValueError('evorationale/*.py not found in --code-root')
    h=hashlib.sha256()
    for path in paths:
        rel=path.relative_to(source).as_posix().encode('utf-8')
        h.update(len(rel).to_bytes(4,'big')+rel)
        h.update(bytes.fromhex(digest(path)))
    return h.hexdigest()

def matches(file, expected, name):
    if not file.is_file(): raise ValueError(f'Missing {name}: {file}')
    got=digest(file)
    if got!=expected:raise ValueError(f'Hash mismatch for {name}: {got} != {expected}')


def evaluate(records, report, scope):
    rows = [r for r in records if scope=='all' or r['temporal_basis_inherited_from_event']!='INTERIM_2024']
    keys = {r['hunk_id'] for r in rows}
    refs = {r['hunk_id']: r for r in rows}
    g = {(r['hunk_id'],s.strip(),POSITIVE[r['relation_candidate']])
         for r in rows if r['relation_candidate'] in POSITIVE
         for s in r['related_atomic_s0_ids'].split(';') if s.strip()}
    # Deduplicate identical predicted link triples, even if multiple verified quotes were emitted.
    evidence = report.get('verified_evidence', [])
    p = {(str(link.get('artifact_id','')),str(link.get('decision_element_id','')),
          str(link.get('relation','')).lower()) for link in evidence
          if str(link.get('artifact_id','')) in keys and
          str(link.get('relation','')).lower() in POSITIVE.values()}
    tp, fp, fn = (p&g, p-g, g-p)
    precision = len(tp)/len(p) if p else 0.0
    recall = len(tp)/len(g) if g else None
    f1 = (2*precision*recall/(precision+recall)) if recall is not None and precision+recall else 0.0
    predicted_hunks={i[0] for i in p}
    negative_hunks={r['hunk_id'] for r in rows if r['relation_candidate'] in ('UNRELATED','IMPLEMENTATION_ONLY')}
    neg_fp={t for t in fp if t[0] in negative_hunks}
    result={
      'scope':scope,
      'evaluated_hunks':len(keys),
      'gold_positive_exact_triples':len(g),
      'predicted_exact_triples':len(p),
      'tp':len(tp), 'fp':len(fp),'fn':len(fn),
      'precision':round(precision,6), 'recall':round(recall,6) if recall is not None else None,
      'f1':round(f1,6),
      'predicted_hunk_coverage':{'count':len(predicted_hunks),'of':len(keys)},
      'fp_on_unrelated_or_implementation_only_hunks':len(neg_fp),
      'unscored_prediction_links_outside_hunk_universe':sum(1 for l in evidence if str(l.get('artifact_id','')) not in keys),
      'limitations':['curated single-repository pilot','not a certified 2024 historical replay',
                     'no gold architecture-outcome labels','offline mode is a deterministic extractive baseline'],
    }
    error_rows=[]
    for verdict, instances in [('TP',tp),('FP',fp),('FN',fn)]:
        for h,e,rel in sorted(instances):
            error_rows.append({'scope':scope,'verdict':verdict,'hunk_id':h,'atomic_s0_id':e,
                               'relation':rel,'reference_hunk_relation':refs[h]['relation_candidate'],
                               'temporal_basis':refs[h]['temporal_basis_inherited_from_event']})
    return result,error_rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frozen',required=True,type=Path)
    p.add_argument('--code-root',required=True,type=Path,help='Unmodified EvoRationale project root')
    p.add_argument('--evaluation',required=True,type=Path,
                   help='Directory from prepare_runtime.py, with run/report.json and run/manifest.json')
    a=p.parse_args()
    root, frozen = a.evaluation.resolve(), a.frozen.resolve()
    prep = read(root / 'PREP_MANIFEST.json')
    if code_tree_hash(a.code_root)!=prep['evorationale_python_tree_sha256']:
        raise ValueError('EvoRationale Python code changed since preparation; refusing to mix run versions')
    fmanifest = read(frozen / 'FREEZE_MANIFEST.json')
    matches(frozen/'FREEZE_MANIFEST.json',prep['frozen_manifest_sha256'],'frozen manifest')
    matches(frozen/'S0_ATOMIC_REVIEWER_CONFIRMED.json',fmanifest['s0_sha256'],'frozen S0')
    for name, expected in fmanifest['reference_sha256'].items():
        matches(frozen/'reference'/name,expected,'frozen '+name)
    matches(root/'inputs'/'S0_RETROSPECTIVE_RUNTIME.json',prep['runtime_s0_sha256'],'runtime S0')
    matches(root/'inputs'/'POST_S0_EVIDENCE_RETROSPECTIVE_53.jsonl',prep['history_sha256'],'unlabeled evidence')
    run_manifest=read(root/'run'/'manifest.json')
    report_file=root/'run'/'report.json'
    matches(report_file,run_manifest['report_sha256'],'model output report')
    if run_manifest['decision_sha256']!=prep['runtime_s0_sha256']:
        raise ValueError('Run used an unexpected S0: refusing to score')
    if run_manifest['history_sha256']!=prep['history_sha256']:
        raise ValueError('Run used unexpected evidence: refusing to score')
    if run_manifest.get('mode')!='offline' or prep.get('mode_planned')!='offline':
        raise ValueError('This evaluator is for the pinned offline first-run baseline only')
    report=read(report_file)
    with (frozen/'reference'/HUNK_FILE).open(encoding='utf-8-sig',newline='') as fp:
        rows=list(csv.DictReader(fp))
    if len(rows)!=30 or len(set(r['hunk_id'] for r in rows))!=30:
        raise ValueError('Expected exactly 30 unique hunk judgments')
    if any(r['relation_candidate'] not in KNOWN for r in rows):
        raise ValueError('Unexpected hunk gold relation value')
    result = {'status':'EXPLORATORY_FROZEN_REFERENCE_OFFLINE_BASELINE',
        'run_id':run_manifest.get('run_id'),
        'run_mode':run_manifest.get('mode'),
        'report_outcome':report.get('recommended_outcome'),
        'verification_status':(report.get('verification') or {}).get('status'),
        'run_sha256':run_manifest['report_sha256'],
        'frozen_s0_sha256':fmanifest['s0_sha256'],
        'historical_replay_certified':False,
        'gold_decision_outcomes_available':False,
        'note':'Research development evaluation; do not claim architecture-outcome accuracy or held-out generalization.',
        'results':{}}
    error_rows=[]
    for scope in EVAL_SCOPES:
        summary, errors=evaluate(rows,report,scope)
        result['results'][scope]=summary
        error_rows.extend(errors)
    dest=root/'score'
    if dest.exists():raise FileExistsError(f'Refusing to overwrite score directory: {dest}')
    dest.mkdir()
    (dest/'metrics.json').write_text(json.dumps(result,ensure_ascii=True,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    with (dest/'link_errors.csv').open('w',encoding='utf-8',newline='') as fp:
        cols=['scope','verdict','hunk_id','atomic_s0_id','relation','reference_hunk_relation','temporal_basis']
        writer=csv.DictWriter(fp,fieldnames=cols);writer.writeheader();writer.writerows(error_rows)
    print(json.dumps(result,indent=2))
    print(f'Scored after the run. Private reference was never copied into agent inputs. Details: {dest}')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(f'ERROR: {exc}',file=sys.stderr);sys.exit(1)
