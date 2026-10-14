#!/usr/bin/env python3
"""Fresh primary hunk effects, versioned scope and separate secondary trace."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
from uuid import uuid4

from _experiment_common import (EXPERIMENT, INPUT_NAMES, MAX_INPUT_TOKENS, MAX_PROVIDER_REQUESTS,
    PROFILE, assert_parent_unchanged, output_snapshot, sha, toolkit_digest, verified_parent, write_new)
from checkpoint_store import CHECKPOINT_POLICY, CheckpointStore


class ForecastResponses:
    """All-negative local transport fixture, never a semantic accuracy test."""
    def __init__(self):
        self.calls = []

    def create(self, **request):
        self.calls.append(deepcopy(request))
        schema = request['text']['format']['schema']['properties']
        fields = schema['reviews']['items']['properties']
        targets = schema['considered_element_ids']['items']['enum']
        reviews = [{'artifact_handle': handle, 'disposition': 'implementation_only',
                    'reason': 'LOCAL FORECAST ONLY; no semantic judgment.',
                    'primary_effects': [], 'secondary_effects': []}
                   for handle in fields['artifact_handle']['enum']]
        return SimpleNamespace(status='completed',
            output_text=json.dumps({'considered_element_ids': targets, 'reviews': reviews}))


def classify(parent, baseline, client, store=None, progress=False):
    from evorationale.budget import Budget, BudgetExhausted
    from evorationale.delta_context import build_delta_catalog
    from evorationale.event_agent import RequestBudgetTracker
    from evorationale.event_context import select_event_batches
    from evorationale.memory import DecisionMemory, MemoryInProcess
    from evorationale.model import artifact_key
    from effect_classifier import PrimaryEffectClassifier
    config = parent['config']['budgets']
    budget = Budget(max_rounds=config['max_rounds'], max_queries=config['max_queries'],
                    max_artifact_reads=config['max_reads'], max_input_tokens=MAX_INPUT_TOKENS,
                    max_output_tokens=16384)
    memory = DecisionMemory(run_id=str(uuid4()), initial_state=deepcopy(parent['state']), status='RUNNING')
    store = store or MemoryInProcess()
    tracker = RequestBudgetTracker(budget, memory, MAX_PROVIDER_REQUESTS)
    model = parent['config']['models']['linker']
    classifier = PrimaryEffectClassifier(model, client=client, baseline_context=baseline)
    selected = select_event_batches(parent['state'], parent['history'], budget.max_artifact_reads)
    planned = selected[:min(budget.max_rounds, budget.max_queries)]
    planned_count = sum(len(batch) for batch in planned)
    reviewed = []
    stop = ''
    store.save(memory)
    for batch in planned:
        memory.round_count += 1
        memory.query_count += 1
        memory.artifact_reads.extend(artifact_key(a) for a in batch)
        catalog = build_delta_catalog(parent['state'], batch)
        handles = list(catalog['artifacts'])
        event = {'round': memory.round_count, 'artifact_keys': [artifact_key(a) for a in batch],
                 'event_identity_sha256': catalog['context']['identity_sha256'], 'focused_chunks': []}
        memory.trace.append(event)
        for offset in range(0, len(handles), 3):
            focus = handles[offset:offset+3]
            chunk = {'focused_artifact_handles': focus, 'status': 'REQUESTED'}
            event['focused_chunks'].append(chunk)
            try:
                rows = classifier.review_chunk(parent['state'], batch, focus, charge=tracker)
                links = classifier.primary_links(parent['state'], batch, rows)
                feedback = deepcopy(classifier.last_feedback)
                chunk.update(status='VALIDATED', reviews=deepcopy(rows), source_feedback=feedback,
                             proof_routing=deepcopy(getattr(classifier, 'last_proof_routing', [])))
                reviewed.extend(artifact_key(catalog['artifacts'][row['artifact_handle']]) for row in rows)
                memory.verifier_feedback.extend(feedback)
                for link in links:
                    memory.record_link(link)
            except BudgetExhausted as exc:
                stop = str(exc)
                chunk.update(status='BUDGET_STOPPED', reason=stop)
            except Exception as exc:
                # Do not print provider exception messages; they may contain
                # echoed source data or transport configuration.
                failure = {'round': memory.round_count, 'focused_artifact_handles': focus,
                           'failure_class': type(exc).__name__, 'phase': 'primary_hunk_effect_review'}
                reason = str(exc)
                failure['technical_reason_code'] = (reason if re.fullmatch(r'[a-z][a-z0-9_]{0,119}', reason)
                                                    else 'provider_or_validation_failure_details_withheld')
                memory.technical_verification_failures.append(failure)
                chunk.update(status='TECHNICAL_FAILURE', failure_class=type(exc).__name__)
                stop = 'technical_classification_failure'
            store.save(memory)
            if progress:
                print(json.dumps({'status': 'PRIMARY_EFFECT_CHUNK_'+chunk['status'],
                    'event_round': memory.round_count, 'reviewed_artifacts': len(reviewed),
                    'planned_artifacts': planned_count, 'provider_requests': len(tracker.requests)}), flush=True)
            if stop:
                break
        if stop:
            break
    complete = len(reviewed) == planned_count and not stop and not memory.technical_verification_failures
    memory.status = 'EXPERIMENT_COMPLETED' if complete else 'EXPERIMENT_INCOMPLETE'
    if not stop:
        stop = 'planned_event_round_limit' if len(planned) < len(selected) else 'selected_sources_exhausted'
    usage = {**tracker.summary(), 'estimated_input_tokens': memory.token_count,
             'rounds': memory.round_count, 'queries': memory.query_count,
             'unique_artifact_reads': len(set(memory.artifact_reads))}
    secondary = [effect for event in memory.trace for chunk in event['focused_chunks']
                 for row in chunk.get('reviews', []) for effect in row['secondary_effects']]
    report = {'experiment_kind': EXPERIMENT, 'investigation_profile': PROFILE,
        'run_id': memory.run_id, 'status': memory.status, 'mode': 'api',
        'source_run_id': parent['run_id'], 'model': model,
        'verified_evidence': deepcopy(memory.verified_links), 'secondary_effects_scored': False,
        'secondary_effect_count': len(secondary), 'budget_usage': usage,
        'coverage': {'planned_event_count': len(planned), 'planned_artifact_count': planned_count,
                     'reviewed_artifact_count': len(reviewed), 'planned_review_complete': complete,
                     'all_history_artifact_count': len(parent['history']),
                     'selected_artifact_count': sum(len(b) for b in selected),
                     'all_history_model_reported_reviewed': len(reviewed) == len(parent['history']),
                     'coverage_note': 'Validated review-row coverage does not certify semantic correctness.'},
        'stopping_reason': stop, 'new_primary_classification': True,
        'independent_semantic_critic': False,
        'source_validation_epistemic_status': 'PROVENANCE_AND_SCHEMA_CHECKED_MODEL_EFFECTS',
        'architecture_outcome': 'NOT_EVALUATED', 'baseline_invalidation_gold_available': False,
        'baseline_context_role': 'PINNED_HISTORICAL_CONTEXT_NOT_FRESH_POST_S0_PROOF',
        'technical_failures': deepcopy(memory.technical_verification_failures),
        'limitations': ['New source-context and primary-effect projection experiment; not identical agent inputs.',
            'Same fixed S0 and 53-source history as parent; added pinned public baseline excerpts.',
            'Semantic roles, primary selection and target-version mapping remain model-assessed.',
            'Secondary source relations are trace evidence, not scored primary predictions.',
            'No architecture outcome or rationale invalidation is established.',
            'Reference has been examined during development; this is not held-out accuracy.']}
    memory.report = report
    store.save(memory)
    return memory, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code-root', required=True, type=Path)
    parser.add_argument('--evaluation', required=True, type=Path, help='Completed scored original v4.9')
    parser.add_argument('--output', required=True, type=Path, help='NEW separate experiment folder')
    parser.add_argument('--baseline-readme', type=Path,
        default=Path(__file__).resolve().parent/'data/public_baseline_README.md')
    parser.add_argument('--mode', choices=['dry-run', 'api'], default='dry-run')
    parser.add_argument('--allow-repository-text-to-api', action='store_true')
    args = parser.parse_args()
    parent = verified_parent(args.code_root, args.evaluation)
    from baseline_context import build_baseline_context
    baseline_raw = args.baseline_readme.read_bytes()
    baseline = build_baseline_context(parent['state'], baseline_raw)
    initial_tool_hash = toolkit_digest()
    output = args.output.resolve()
    if args.mode == 'api' and output.exists():
        if (output/'RUN_RECEIPT.json').is_file():
            _, _, receipt, protocol, report = output_snapshot(output, parent['code_root'])
            if (protocol['source_member_sha256'] != parent['hashes']
                    or protocol['baseline_readme_sha256'] != sha(baseline_raw)):
                raise ValueError('Existing experiment belongs to different source/context')
            if not report['coverage']['planned_review_complete']:
                raise FileExistsError('Preserve incomplete experiment; choose a NEW output only after inspection')
            print(json.dumps({'status': 'EXISTING_PRIMARY_EFFECT_EXPERIMENT_VERIFIED_NO_API_CALLED',
                              'run_id': receipt['run_id'], 'output': str(output/'run/report.json')}, indent=2))
            return
        raise FileExistsError('Preserve partial experiment; inspect before selecting a NEW output')
    if args.mode == 'dry-run':
        fake = ForecastResponses()
        memory, report = classify(parent, baseline, SimpleNamespace(responses=fake))
        assert_parent_unchanged(parent)
        if toolkit_digest() != initial_tool_hash or args.baseline_readme.read_bytes() != baseline_raw:
            raise ValueError('Experiment code/context changed during forecast')
        complete = report['coverage']['planned_review_complete']
        print(json.dumps({'status': 'PRIMARY_EFFECT_DRY_RUN_NO_API_CALLED', 'experiment_kind': EXPERIMENT,
            'mock_primary_requests': len(fake.calls), 'independent_critic_requests': 0,
            'forecast_complete': complete, 'forecast_input_estimate': memory.token_count,
            'forecast_within_input_ceiling': complete and memory.token_count <= MAX_INPUT_TOKENS,
            'max_input_tokens': MAX_INPUT_TOKENS, 'max_provider_requests': MAX_PROVIDER_REQUESTS,
            'coverage': report['coverage'], 'baseline_selected_line_count': baseline['selected_line_count'],
            'toolkit_sha256': initial_tool_hash, 'technical_failures': report['technical_failures'],
            'output_created': False, 'hosted_accuracy_available': False,
            'note': 'Local all-negative fixtures forecast request envelopes, not F1.'}, indent=2))
        if not complete:
            raise RuntimeError('Forecast incomplete; inspect limits/errors before a paid run')
        return
    if not args.allow_repository_text_to_api:
        raise PermissionError('API mode requires --allow-repository-text-to-api')
    if not os.environ.get('OPENAI_API_KEY', '').strip():
        raise RuntimeError('OPENAI_API_KEY missing; do not print the secret')
    from openai import OpenAI
    client = OpenAI(max_retries=0)
    output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    write_new(output/'RUN_ATTEMPT.json', {'status': 'PRIMARY_EFFECT_ATTEMPT_STARTED',
        'source_run_id': parent['run_id'], 'start_utc': started, 'toolkit_sha256': initial_tool_hash})
    (output/'inputs').mkdir()
    raw_inputs = [parent['members']['inputs/'+INPUT_NAMES[0]],
                  parent['members']['inputs/'+INPUT_NAMES[1]], baseline_raw]
    for name, raw in zip(INPUT_NAMES, raw_inputs):
        with (output/'inputs'/name).open('xb') as stream:
            stream.write(raw)
    config = parent['config']
    protocol = {'experiment_kind': EXPERIMENT, 'mode': 'api', 'toolkit_sha256': initial_tool_hash,
        'source_core_sha256': config['v49_python_sha256'], 'source_run_id': parent['run_id'],
        'source_evaluation': str(parent['evaluation']), 'source_member_sha256': parent['hashes'],
        'runtime_s0_sha256': sha(raw_inputs[0]), 'history_sha256': sha(raw_inputs[1]),
        'baseline_readme_sha256': sha(raw_inputs[2]), 'baseline_context': baseline,
        'frozen_manifest_sha256': config['frozen_manifest_sha256'], 'frozen_s0_sha256': config['frozen_s0_sha256'],
        'model': config['models']['linker'], 'parent_budget': config['budgets'],
        'new_budget': {'max_input_tokens': MAX_INPUT_TOKENS, 'max_provider_requests': MAX_PROVIDER_REQUESTS},
        'max_rounds': config['budgets']['max_rounds'], 'max_reads': config['budgets']['max_reads'],
        'max_queries': config['budgets']['max_queries'], 'gold_labels_in_agent_inputs': False,
        'checkpoint_write_policy': CHECKPOINT_POLICY,
        'prediction_unit': 'ONE_PRIMARY_RELATION_TYPE_PER_HUNK_WITH_PRIMARY_TARGET_IDS',
        'secondary_relations_scored': False, 'independent_semantic_critic': False,
        'comparison_note': 'Same fixed S0/history; added public baseline context and changed prediction projection/semantic policy. Not identical inference inputs or equal-compute comparison.'}
    write_new(output/'PROTOCOL.json', protocol)
    print('Running fresh primary-effect experiment; API usage may incur costs.', flush=True)
    memory, report = classify(parent, baseline, client, CheckpointStore(output/'working_checkpoints'), progress=True)
    assert_parent_unchanged(parent)
    if toolkit_digest() != initial_tool_hash or args.baseline_readme.read_bytes() != baseline_raw:
        raise ValueError('Code/context changed; preserve progress, no completed receipt')
    for name, raw in zip(INPUT_NAMES, raw_inputs):
        if (output/'inputs'/name).read_bytes() != raw:
            raise ValueError('Inputs changed; preserve progress, no completed receipt')
    (output/'run').mkdir(); (output/'checkpoints').mkdir()
    write_new(output/'run/report.json', report)
    checkpoint_name = 'checkpoints/'+memory.run_id+'.json'
    write_new(output/checkpoint_name, memory.asdict())
    manifest = {'experiment_kind': EXPERIMENT, 'investigation_profile': PROFILE, 'mode': 'api',
                'run_id': memory.run_id, 'source_run_id': parent['run_id'],
                'protocol_sha256': sha((output/'PROTOCOL.json').read_bytes()),
                'report_sha256': sha((output/'run/report.json').read_bytes())}
    write_new(output/'run/manifest.json', manifest)
    receipt = {'status': EXPERIMENT+'_COMPLETED_AND_HASHED', 'experiment_kind': EXPERIMENT, 'mode': 'api',
        'run_id': memory.run_id, 'source_run_id': parent['run_id'], 'model': protocol['model'],
        'start_utc': started, 'finish_utc': datetime.now(timezone.utc).isoformat(),
        'toolkit_sha256': initial_tool_hash, 'protocol_sha256': manifest['protocol_sha256'],
        'run_report_sha256': manifest['report_sha256'],
        'run_manifest_sha256': sha((output/'run/manifest.json').read_bytes()),
        'checkpoint_relative_path': checkpoint_name, 'checkpoint_sha256': sha((output/checkpoint_name).read_bytes())}
    write_new(output/'RUN_RECEIPT.json', receipt)
    output_snapshot(output, parent['code_root'])
    print(json.dumps({'status': receipt['status'], 'run_id': memory.run_id,
                     'output': str(output/'run/report.json'), 'primary_requests': report['budget_usage']['provider_requests_reserved'],
                     'planned_review_complete': report['coverage']['planned_review_complete'],
                     'technical_failures': len(report['technical_failures']), 'hosted_f1': 'NOT_SCORED_YET'}, indent=2))
    if not report['coverage']['planned_review_complete']:
        raise RuntimeError('Incomplete classification preserved; inspect before any further API run')


if __name__ == '__main__':
    main()
