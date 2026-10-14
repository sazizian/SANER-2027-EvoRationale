#!/usr/bin/env python3
"""Recheck frozen v4.9 primary hypotheses; never repeat primary API requests."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from types import SimpleNamespace

from _kit_common import (EXPERIMENT, INPUT_NAMES, MAX_INPUT_TOKENS, MAX_PROVIDER_REQUESTS,
    PROFILE, assert_parent_unchanged, output_snapshot, sha, toolkit_digest, verified_parent, write_new)


class ForecastResponses:
    """Local all-reject fixture for envelopes only, not semantic predictions."""
    def __init__(self):
        self.calls = []

    def create(self, **request):
        self.calls.append(deepcopy(request))
        properties = request['text']['format']['schema']['properties']
        if set(properties) != {'decisions'}:
            raise AssertionError('Cached replay attempted a primary classification request')
        fields = properties['decisions']['items']['properties']
        ids = fields['candidate_id']['enum']
        decisions = []
        for candidate_id in ids:
            row = {name: False if descriptor['type'] == 'boolean' else
                   'LOCAL FORECAST ONLY; no semantic judgment or accuracy result.'
                   for name, descriptor in fields.items()}
            row.update(candidate_id=candidate_id, verdict='reject')
            decisions.append(row)
        return SimpleNamespace(status='completed', output_text=json.dumps({'decisions': decisions}))


def create_agent(parent, cache, client):
    from evorationale.budget import Budget
    from evorationale.delta_linking import NoNomination
    from evorationale.event_agent import EventReviewAgent
    from scope_checker import ScopedReplayJudge
    old = parent['config']['budgets']
    judge = ScopedReplayJudge(parent['config']['models']['judge'], cache, client=client)
    agent = EventReviewAgent(linker=NoNomination(), judge=judge, profile='event-pair-reviewed',
        max_provider_requests=MAX_PROVIDER_REQUESTS,
        budget=Budget(max_rounds=old['max_rounds'], max_queries=old['max_queries'],
                      max_artifact_reads=old['max_reads'], max_input_tokens=MAX_INPUT_TOKENS,
                      max_output_tokens=16384))
    return agent, judge


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code-root', required=True, type=Path, help='Unchanged v4.9 code folder')
    parser.add_argument('--evaluation', required=True, type=Path, help='Completed original v4.9 evaluation')
    parser.add_argument('--output', required=True, type=Path, help='NEW isolated experiment folder')
    parser.add_argument('--mode', choices=['dry-run', 'api'], default='dry-run')
    parser.add_argument('--allow-repository-text-to-api', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    parent = verified_parent(args.code_root, args.evaluation)
    from scope_checker import CachedEventReviews
    cache = CachedEventReviews(parent['state'], parent['history'], parent['checkpoint'],
                               max_reads=parent['config']['budgets']['max_reads'])
    initial_tool_hash = toolkit_digest()
    if args.mode == 'api' and output.exists():
        if (output/'RUN_RECEIPT.json').is_file():
            _, _, receipt, protocol, _ = output_snapshot(output, parent['code_root'])
            if (receipt['source_run_id'] != parent['run_id']
                    or protocol['source_member_sha256'] != parent['hashes']):
                raise ValueError('Existing experiment belongs to a different primary cache')
            print(json.dumps({'status': 'EXISTING_SCOPE_EXPERIMENT_VERIFIED_NO_API_CALLED',
                              'run_id': receipt['run_id'], 'output': str(output/'run/report.json')}, indent=2))
            return
        raise FileExistsError('Preserve incomplete scope experiment; choose a NEW output folder')
    if args.mode == 'dry-run':
        fake = ForecastResponses()
        agent, _ = create_agent(parent, cache, SimpleNamespace(responses=fake))
        run = agent.run(parent['state'], parent['history'])
        assert_parent_unchanged(parent)
        if toolkit_digest() != initial_tool_hash:
            raise ValueError('Experiment code changed during forecast')
        forecast_complete = (len(fake.calls) == cache.candidate_event_count
            and len(run.memory.trace) == len(cache.batches)
            and not run.memory.technical_verification_failures
            and run.report['stopping_reason'] not in
                {'cumulative_input_token_limit', 'provider_request_limit'})
        print(json.dumps({'status': 'SCOPE_RECHECK_DRY_RUN_NO_API_CALLED',
            'experiment_kind': EXPERIMENT, 'primary_predictions': 'CACHED_V49_UNCHANGED',
            'new_primary_api_requests': 0, 'mock_checker_requests': len(fake.calls),
            'forecast_input_estimate': run.memory.token_count,
            'forecast_complete': forecast_complete,
            'forecast_within_input_ceiling': forecast_complete and run.memory.token_count <= MAX_INPUT_TOKENS,
            'max_input_tokens': MAX_INPUT_TOKENS, 'max_provider_requests': MAX_PROVIDER_REQUESTS,
            'cache_batches': len(cache.batches), 'model': parent['config']['models']['judge'],
            'source_run_id': parent['run_id'], 'toolkit_sha256': initial_tool_hash,
            'technical_failures': run.memory.technical_verification_failures,
            'stopping_reason': run.report['stopping_reason'],
            'output_created': False, 'hosted_accuracy_available': False,
            'note': 'All-reject local fixture forecasts request envelopes only; no F1 is measured.'}, indent=2))
        if not forecast_complete:
            raise RuntimeError('Local checker forecast did not finish all cached events; inspect limits/errors')
        return
    if not args.allow_repository_text_to_api:
        raise PermissionError('Real checker calls require --allow-repository-text-to-api')
    if not os.environ.get('OPENAI_API_KEY', '').strip():
        raise RuntimeError('OPENAI_API_KEY is missing; do not print the secret')
    from openai import OpenAI
    # Validate SDK construction before claiming the new directory. Automatic
    # SDK retries stay disabled; the structured-response retry limit is explicit.
    client = OpenAI(max_retries=0)
    agent, _ = create_agent(parent, cache, client)
    output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    write_new(output/'RUN_ATTEMPT.json', {'status': 'SCOPE_RECHECK_ATTEMPT_STARTED',
        'start_utc': started, 'source_run_id': parent['run_id'], 'toolkit_sha256': initial_tool_hash})
    (output/'inputs').mkdir()
    input_bytes = [parent['members']['inputs/' + INPUT_NAMES[0]],
                   parent['members']['inputs/' + INPUT_NAMES[1]],
                   parent['members'][parent['checkpoint_name']]]
    for name, raw in zip(INPUT_NAMES, input_bytes):
        with (output/'inputs'/name).open('xb') as stream:
            stream.write(raw)
    config = parent['config']
    protocol = {'experiment_kind': EXPERIMENT, 'mode': 'api', 'toolkit_sha256': initial_tool_hash,
        'source_core_sha256': config['v49_python_sha256'], 'source_run_id': parent['run_id'],
        'source_evaluation': str(parent['evaluation']), 'source_member_sha256': parent['hashes'],
        'runtime_s0_sha256': sha(input_bytes[0]), 'history_sha256': sha(input_bytes[1]),
        'source_checkpoint_sha256': sha(input_bytes[2]),
        'frozen_manifest_sha256': config['frozen_manifest_sha256'],
        'frozen_s0_sha256': config['frozen_s0_sha256'], 'model': config['models']['judge'],
        'original_budget': config['budgets'],
        'new_budget': {'max_input_tokens': MAX_INPUT_TOKENS, 'max_provider_requests': MAX_PROVIDER_REQUESTS},
        'gold_labels_in_agent_inputs': False, 'new_primary_api_requests': 0,
        'note': 'Cached-primary ablation; include original classification cost in full-pipeline comparisons.'}
    write_new(output/'PROTOCOL.json', protocol)
    # Keep per-round progress separately from the immutable final checkpoint.
    # Interrupted experiments are preserved, never silently restarted.
    from evorationale.memory import FileMemory
    agent.store = FileMemory(output/'working_checkpoints')
    print('Running cached-primary scope checker experiment; API usage may incur costs.', flush=True)
    run = agent.run(parent['state'], parent['history'])
    assert_parent_unchanged(parent)
    if toolkit_digest() != initial_tool_hash:
        raise ValueError('Experiment code changed during checker execution; no completion receipt')
    for name, raw in zip(INPUT_NAMES, input_bytes):
        if (output/'inputs'/name).read_bytes() != raw:
            raise ValueError('Experiment inputs changed during execution; no completion receipt')
    report = run.report
    report.update(experiment_kind=EXPERIMENT, investigation_profile=PROFILE,
        primary_prediction_origin='CACHED_V49_PRIMARY', source_run_id=parent['run_id'],
        new_primary_api_requests=0, comparison_note=protocol['note'])
    report['investigation_coverage']['classification_policy'] = (
        'Validated cached v4.9 pair outcomes; no new primary classification. '
        'Only positive cached hypotheses receive new typed scope checks. '
        'Original source guards still apply; alignment fields are model assessments.')
    run.memory.report = report
    (output/'run').mkdir()
    (output/'checkpoints').mkdir()
    write_new(output/'run/report.json', report)
    checkpoint_name = 'checkpoints/' + run.memory.run_id + '.json'
    write_new(output/checkpoint_name, run.memory.asdict())
    report_hash = sha((output/'run/report.json').read_bytes())
    protocol_hash = sha((output/'PROTOCOL.json').read_bytes())
    manifest = {'run_id': run.memory.run_id, 'mode': 'api', 'experiment_kind': EXPERIMENT,
        'investigation_profile': PROFILE, 'protocol_sha256': protocol_hash,
        'report_sha256': report_hash, 'source_run_id': parent['run_id']}
    write_new(output/'run/manifest.json', manifest)
    receipt = {'status': EXPERIMENT + '_COMPLETED_AND_HASHED', 'mode': 'api',
        'experiment_kind': EXPERIMENT, 'run_id': run.memory.run_id, 'source_run_id': parent['run_id'],
        'model': protocol['model'], 'start_utc': started, 'finish_utc': datetime.now(timezone.utc).isoformat(),
        'protocol_sha256': protocol_hash, 'toolkit_sha256': initial_tool_hash,
        'run_report_sha256': report_hash,
        'run_manifest_sha256': sha((output/'run/manifest.json').read_bytes()),
        'checkpoint_relative_path': checkpoint_name, 'checkpoint_sha256': sha((output/checkpoint_name).read_bytes())}
    write_new(output/'RUN_RECEIPT.json', receipt)
    output_snapshot(output, parent['code_root'])
    print(json.dumps({'status': receipt['status'], 'run_id': receipt['run_id'],
        'output': str(output/'run/report.json'), 'new_provider_requests': report['budget_usage']['provider_requests_reserved'],
        'technical_failures': len(run.memory.technical_verification_failures),
        'hosted_f1': 'NOT_SCORED_YET'}, indent=2))


if __name__ == '__main__':
    main()
