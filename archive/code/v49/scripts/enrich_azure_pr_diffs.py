"""Enrich an existing Azure AVNM pilot with auditable *current* GitHub PR file diffs.

DOES NOT replace old inputs, backdate mutable PR diffs, auto-approve S0, or
claim completeness/historical replay. Fetches the same PR numbers selected by
an existing capture manifest, not hand-picked after examining model outcomes.

Usage (from project root):
  python scripts/enrich_azure_pr_diffs.py \
    --decision examples/azure/pilot_snapshot/decision_state_ATOMIC_APPROVED.json \
    --history examples/azure/pilot_snapshot/history_LIVE.jsonl \
    --capture-manifest examples/azure/pilot_snapshot/github_capture_manifest.json \
    --output data/azure_avnm_diff_v41
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
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from typing import Any

# Support direct script execution with no installed package, as in v4.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from evorationale.model import (validate_state, normalize_history, normalize_artifact,
                                 parse_timestamp, iso)

API_BASE = 'https://api.github.com'
ALLOWED_REPO = 'Azure/Enterprise-Scale'
PATH_SUFFIXES = ('eslzarm.json', 'eslz-portal.json')
GITHUB_HEADERS = {'Accept': 'application/vnd.github+json',
                  'User-Agent': 'EvoRationale-auditable-pilot-v4.1',
                  'X-GitHub-Api-Version': '2022-11-28'}


def _json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode('utf-8')


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def api_get(path: str, token: str | None = None) -> Any:
    if not path.startswith('/repos/Azure/Enterprise-Scale/pulls/'):
        raise ValueError('Unapproved GitHub API endpoint')
    headers = dict(GITHUB_HEADERS)
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = Request(API_BASE + path, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        if exc.code in (403, 429):
            raise RuntimeError('GitHub rate limit or access denied; set GITHUB_TOKEN securely in the environment, not in code') from exc
        raise RuntimeError(f'GitHub read failed (HTTP {exc.code}); no output overwritten') from exc


def relevant_file(path: str) -> bool:
    # Predeclared policy: decision's ARM/portal files + AVNM-specific templates.
    lowered = path.replace('\\', '/').lower()
    return lowered.startswith('eslzarm/') and (lowered.endswith(PATH_SUFFIXES) or
                                                 'avnm' in lowered.split('/')[-1])


def _added_patch_window(patch: str, line_index: int, max_chars: int = 520) -> tuple[str, int, int] | None:
    lines = patch.splitlines()
    # Stay within one hunk to avoid splicing unrelated code changes.
    section_start = line_index
    while section_start > 0 and not lines[section_start-1].startswith('@@'):
        section_start -= 1
    section_end = line_index + 1
    while section_end < len(lines) and not lines[section_end].startswith('@@'):
        section_end += 1
    # Include the matched addition, nearby added JSON lines and context.
    start, end = line_index, line_index+1
    if len(lines[line_index]) > max_chars:
        return None
    while True:
        choices = []
        if start > section_start:
            choices.append((start-1, end))
        if end < section_end:
            choices.append((start, end+1))
        # Prefer context that extends the surrounding JSON block, but never cross a hunk.
        fitting = [(s,e) for s,e in choices if len('\n'.join(lines[s:e])) <= max_chars]
        if not fitting:
            break
        fitting.sort(key=lambda se: (-(se[1]-se[0]), abs(line_index-(se[0]+se[1]-1)/2), se[0]))
        next_start,next_end = fitting[0]
        if next_start == start and next_end == end:
            break
        start,end = next_start,next_end
    return '\n'.join(lines[start:end]),start+1,end


def diff_excerpts(patch: str, filename: str, number: int, max_per_file: int = 24) -> list[dict[str, Any]]:
    """Contiguous excerpts around AVNM added lines; no fabricated code text."""
    if not relevant_file(filename):
        return []
    lines = patch.splitlines()
    hits=[]
    for i,line in enumerate(lines):
        if not line.startswith('+') or line.startswith('+++'):
            continue
        if not re.search(r'avnm|virtualnetworkmanager',line,re.I):
            continue
        found=_added_patch_window(patch,i)
        if found is not None:
            chunk,start,end=found
            # An extractive quote can include this source-path header; the
            # header is collector metadata, not a verbatim line from the diff.
            header=f'GitHub PR #{number} added ARM/portal code for AVNM in {filename}:\n'
            content=header+chunk
            if len(content)<=650 and content not in [x['content'] for x in hits]:
                hits.append({'content': content, 'patch_line_start':start,
                             'patch_line_end':end, 'raw_patch_excerpt':chunk})
        if len(hits)>=max_per_file:
            break
    return hits


def _write_json(path:Path,value:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(_json_bytes(value))


def enrich(*, decision_path:Path, history_path:Path, capture_manifest_path:Path, output_dir:Path,
           requester=api_get, clock=None, token: str|None = None,
           max_pages:int = 10, max_snippets_per_file:int = 24) -> dict[str,Any]:
    if max_pages<1 or max_snippets_per_file<1:
        raise ValueError('Positive bounds required')
    state=validate_state(json.loads(decision_path.read_text(encoding='utf-8')))
    if state['repository'] != ALLOWED_REPO:
        raise ValueError('This bounded pilot is restricted to Azure/Enterprise-Scale')
    original_history=normalize_history([json.loads(line) for line in history_path.read_text(encoding='utf-8').splitlines() if line.strip()])
    if any(item['repository']!=ALLOWED_REPO for item in original_history):
        raise ValueError('Mixed repository in original history')
    manifest=json.loads(capture_manifest_path.read_text(encoding='utf-8'))
    pr_numbers=manifest.get('selected_pr_numbers')
    if not isinstance(pr_numbers,list) or not pr_numbers or not all(type(n) is int and 0<n<=9999999 for n in pr_numbers):
        raise ValueError('Capture manifest must specify valid selected_pr_numbers')
    if len(set(pr_numbers))!=len(pr_numbers):
        raise ValueError('Duplicate PR numbers in capture manifest')
    if len(pr_numbers)>15:
        raise ValueError('Safety cap: at most 15 preselected PRs')
    if manifest.get('repository') != ALLOWED_REPO:
        raise ValueError('Capture manifest repository mismatch')
    clock=clock or (lambda: datetime.now(timezone.utc))
    started=clock()
    if started.tzinfo is None:
        raise ValueError('Capture timestamp must include timezone')
    started=started.astimezone(timezone.utc)
    found=[]
    raw_response={}
    pages_per_pr={}
    gaps=[]
    source_stats=[]
    for n in sorted(pr_numbers):
        # The base selection is fixed by the original manifest. The collector
        # NEVER discovers new PR numbers based on what the agent hoped to find.
        collected=[]
        page=1
        while page<=max_pages:
            endpoint=f'/repos/Azure/Enterprise-Scale/pulls/{n}/files?per_page=100&page={page}'
            response=requester(endpoint,token)
            if not isinstance(response,list):
                raise ValueError(f'GitHub PR {n} file listing is not an array')
            if len(response)>100:
                raise ValueError('Unreasonable GitHub page length')
            raw_response[f'pr_{n}_files_page_{page}']=response
            collected.extend(response)
            if len(response)<100:
                break
            page+=1
        pages_per_pr[str(n)]=len([key for key in raw_response if key.startswith(f'pr_{n}_')])
        if len(response)==100 and page>max_pages:
            gaps.append({'pr':n,'reason':'PAGINATION_LIMIT_REACHED','max_pages':max_pages})
        for f in collected:
            filename=f.get('filename')
            if not isinstance(filename,str) or not relevant_file(filename):
                continue
            patch=f.get('patch')
            if not isinstance(patch,str) or not patch:
                gaps.append({'pr':n,'file':filename,'reason':'PATCH_MISSING_FROM_GITHUB_API'})
                continue
            raw_sha=hashlib.sha256(patch.encode('utf-8')).hexdigest()
            snippets=diff_excerpts(patch,filename,n,max_snippets_per_file)
            if len(snippets)>=max_snippets_per_file:
                gaps.append({'pr':n,'file':filename,'reason':'EXCERPT_SAMPLING_CAP_REACHED',
                             'limit':max_snippets_per_file})
            source_stats.append({'pr':n,'file':filename,'patch_sha256':raw_sha,
                                 'excerpts':len(snippets),'file_status':f.get('status')})
            for i,snip in enumerate(snippets,1):
                observed=clock()
                if observed.tzinfo is None:
                    raise ValueError('Audit clock must include timezone')
                observed=observed.astimezone(timezone.utc)
                if observed < started:
                    raise ValueError('Non-monotonic capture clock')
                path_hash=hashlib.sha256(filename.encode()).hexdigest()[:12]
                row={
                    'artifact_id':f'github-pr-diff-{n}-{path_hash}-{i:03d}',
                    'repository':ALLOWED_REPO,
                    'source_type':'pull_request_diff_excerpt',
                    'source_location':f'https://github.com/Azure/Enterprise-Scale/pull/{n}/files',
                    'title':f'PR #{n} changed code in {filename}',
                    'content':snip['content'],
                    'timestamp':iso(observed.isoformat()),
                    'first_auditable_at':iso(observed.isoformat()),
                    'tags':['github_diff','AVNM','current_snapshot'],
                    'metadata':{
                        'source_kind':'CURRENT_PR_PATCH_SNAPSHOT',
                        'historical_replay_safe':False,
                        'excerpt_truncated':True,
                        'immutable_source_object':False,
                        'file_path':filename,'parent_pr':n,
                        'patch_sha256':raw_sha,'raw_patch_line_start':snip['patch_line_start'],
                        'raw_patch_line_end':snip['patch_line_end'],
                        'derived_header_note':'File name and PR number in first line were added by the collector; remaining lines are exact contiguous source patch text.',
                    },
                }
                found.append(normalize_artifact(row))
    ended=clock()
    if ended.tzinfo is None:
        raise ValueError('Clock must include timezone')
    ended=ended.astimezone(timezone.utc)
    cutoff=iso((ended+timedelta(seconds=2)).isoformat())
    if parse_timestamp(state['accepted_at']) >= parse_timestamp(cutoff):
        raise ValueError('Capture cutoff not after decision acceptance')
    draft=deepcopy(state)
    draft['cutoff_at']=cutoff
    draft['episode_id']=state['episode_id']+'-diff-enrichment-v41'
    draft['research_label']='EXPLORATORY_DIFF_AUGMENTATION_NOT_HISTORICAL_REPLAY'
    draft['snapshot_note']='Diff excerpts captured now; historical body versions not independently reconstructed.'
    draft['human_approved']=False
    draft['human_review_required']=True
    draft['builder_status']='DIFF_ENRICHED_DRAFT_REQUIRES_HUMAN_APPROVAL'
    draft['source_history_sha256']=file_sha(history_path)
    draft['derived_from_approved_decision_sha256']=file_sha(decision_path)
    validate_state(draft,require_approved=False)
    merged=normalize_history(original_history+found)
    out_hist=''.join(json.dumps(item,sort_keys=True,ensure_ascii=False)+'\n' for item in merged).encode('utf-8')
    # All outputs are new; refuse to overwrite a previous scientific run.
    if output_dir.exists():
        raise FileExistsError(f'Output directory already exists: {output_dir}. Choose a new output path.')
    if not found:
        raise RuntimeError('No AVNM added-line snippets found. Nothing written; inspect GitHub API source diffs.')
    output_dir.mkdir(parents=True)
    (output_dir/'history_ENRICHED.jsonl').write_bytes(out_hist)
    _write_json(output_dir/'decision_state_ENRICHED_DRAFT.json',draft)
    for key,value in raw_response.items():
        _write_json(output_dir/'raw_api'/f'{key}.json',value)
    info={
        'mode':'CURRENT_DIFF_CAPTURE_EXPLORATORY',
        'source_repository':ALLOWED_REPO,
        'selected_pr_numbers':sorted(pr_numbers),
        'selected_pr_policy':'ALL original manifest PR numbers; only eslzArm.json, eslz-portal.json and filename-containing-avnm templates',
        'capture_started_at':iso(started.isoformat()),
        'capture_completed_at':iso(ended.isoformat()),
        'proposed_cutoff':cutoff,
        'old_artifact_versions':len(original_history),
        'new_diff_excerpt_versions':len(found),
        'total_artifact_versions':len(merged),
        'old_decision_sha256':file_sha(decision_path),
        'old_history_sha256':file_sha(history_path),
        'enriched_history_sha256':hashlib.sha256(out_hist).hexdigest(),
        'diff_source_files':source_stats,
        'capture_gaps':gaps,
        'pages_per_pr':pages_per_pr,
        'historical_replay_certified':False,
        'independently_adjudicated_ground_truth_available':False,
        'note':'A patch line shows an implementation change in the captured diff; it is not proof the design rationale remained optimal. No S0 was auto-approved.',
    }
    _write_json(output_dir/'diff_capture_manifest.json',info)
    return info


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--decision',type=Path,required=True)
    p.add_argument('--history',type=Path,required=True)
    p.add_argument('--capture-manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--max-pages',type=int,default=10)
    p.add_argument('--max-snippets-per-file',type=int,default=24)
    args=p.parse_args()
    info=enrich(decision_path=args.decision, history_path=args.history,
                capture_manifest_path=args.capture_manifest,output_dir=args.output,
                max_pages=args.max_pages,max_snippets_per_file=args.max_snippets_per_file,
                token=os.getenv('GITHUB_TOKEN'))
    print(json.dumps({'status':'DRAFT_REQUIRES_HUMAN_REVIEW','original_unchanged':True,
                      'new_diff_excerpt_versions':info['new_diff_excerpt_versions'],
                      'total_artifact_versions':info['total_artifact_versions'],
                      'historical_replay_certified':False,'output':str(args.output)},indent=2))

if __name__=='__main__':
    main()
