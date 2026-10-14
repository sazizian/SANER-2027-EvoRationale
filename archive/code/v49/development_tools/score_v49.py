#!/usr/bin/env python3
"""Score a completed v4.9 development run using the unchanged exact-triple scorer.

No label rows are read before the completed-run and frozen-reference hashes pass.
Comparisons describe development examples; they do not establish generalization.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import shutil
import tempfile

from _score_core import EVAL_SCOPES, HUNK_FILE, KNOWN, code_tree_hash, digest, evaluate, matches, read
from bundle_v49_diagnostics import verified_members
from prepare_v49 import COMPARISON_NOTE, DECISION, HISTORY, KIND, MODEL_CHANGE_NOTE, POLICY_CHANGE_NOTE, PROFILE, SEMANTIC_PHASE_CONFIG, save, validate_prepared_configuration


def previous_metrics(path: Path, pinned: dict | None, version: int, frozen_s0_sha256: str):
    if not pinned:
        raise ValueError(f'Previous v{version/10:.1f} was not pinned during preparation')
    for relative, key in [('RUN_RECEIPT.json', 'receipt_sha256'), ('DEV_PREP_MANIFEST.json', 'config_sha256'),
                          ('run/manifest.json', 'run_manifest_sha256'), ('run/report.json', 'report_sha256'),
                          ('score/metrics.json', 'score_sha256'), ('inputs/'+DECISION, 'runtime_s0_sha256'),
                          ('inputs/'+HISTORY, 'history_sha256')]:
        matches(path/relative, pinned[key], f'previous v{version/10:.1f} '+relative)
    if version in {45, 46, 47, 48}:
        matches(path/pinned['checkpoint_relative_path'], pinned['checkpoint_sha256'], f'previous v{version/10:.1f} checkpoint')
        if version == 48:
            from bundle_v48_diagnostics import verified_members as verify_previous
        elif version == 47:
            from bundle_v47_diagnostics import verified_members as verify_previous
        elif version == 46:
            from bundle_v46_diagnostics import verified_members as verify_previous
        else:
            from bundle_v45_diagnostics import verified_members as verify_previous
        verify_previous(path)
    metrics = read(path/'score'/'metrics.json')
    if (metrics.get('frozen_s0_sha256') != frozen_s0_sha256
            or metrics.get(f'v{version}_run_report_sha256') != pinned['report_sha256']):
        raise ValueError('Previous score provenance mismatch')
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation', type=Path, required=True)
    parser.add_argument('--frozen', type=Path, required=True)
    parser.add_argument('--code-root', type=Path, required=True)
    parser.add_argument('--original-api', type=Path, required=True)
    parser.add_argument('--original-offline', type=Path, required=True)
    parser.add_argument('--previous-v43', type=Path, required=True)
    parser.add_argument('--previous-v44', type=Path, required=True)
    parser.add_argument('--previous-v45', type=Path, required=True)
    parser.add_argument('--previous-v46', type=Path, required=True)
    parser.add_argument('--previous-v47', type=Path, required=True)
    parser.add_argument('--previous-v48', type=Path, required=True)
    parser.add_argument('--previous-v42', type=Path)
    args = parser.parse_args()
    ev, frozen, source, offline = (p.resolve() for p in
                                   (args.evaluation, args.frozen, args.original_api, args.original_offline))
    if (ev/'score').is_symlink():
        raise FileExistsError('Refuse a symlink score destination')
    config = read(ev/'DEV_PREP_MANIFEST.json')
    receipt = read(ev/'RUN_RECEIPT.json')
    validate_prepared_configuration(config)
    if (config.get('kind') != KIND or config.get('investigation_profile') != PROFILE
            or receipt.get('status') != 'V49_DEV_HOSTED_RUN_COMPLETED_AND_HASHED'
            or receipt.get('mode') != 'api' or receipt.get('investigation_profile') != PROFILE):
        raise ValueError('Missing completed, attested v4.9 event-pair-reviewed run')
    matches(ev/'DEV_PREP_MANIFEST.json', receipt['prep_sha256'], 'v4.9 preparation')
    if (code_tree_hash(args.code_root) != config['v49_python_sha256']
            or receipt['code_tree_sha256'] != config['v49_python_sha256']
            or receipt.get('model') != config.get('models')
            or receipt.get('nominal_budgets') != config.get('budgets')
            or receipt.get('parent_v44_models') != config.get('parent_v44_models')
            or receipt.get('parent_v45_models') != config.get('parent_v45_models')
            or receipt.get('parent_v46_models') != config.get('parent_v46_models')
            or receipt.get('parent_v47_models') != config.get('parent_v47_models')
            or receipt.get('parent_v48_models') != config.get('parent_v48_models')
            or receipt.get('semantic_phase_config') != config.get('semantic_phase_config')
            or config.get('semantic_phase_config') != SEMANTIC_PHASE_CONFIG
            or receipt.get('policy_change_note') != config.get('policy_change_note')):
        raise ValueError('v4.9 source or model configuration changed')
    if (config.get('nomination_mode') != 'none'
            or receipt.get('nomination_mode') != config['nomination_mode']):
        raise ValueError('v4.9 nomination mode changed')
    matches(ev/'inputs'/DECISION, config['runtime_s0_sha256'], 'runtime S0')
    matches(ev/'inputs'/HISTORY, config['history_sha256'], 'unlabeled history')
    matches(ev/'run'/'manifest.json', receipt['run_manifest_sha256'], 'run manifest')
    manifest = read(ev/'run'/'manifest.json')
    matches(ev/'run'/'report.json', receipt['run_report_sha256'], 'run report')
    if (manifest.get('mode') != 'api' or manifest.get('investigation_profile') != PROFILE
            or manifest.get('run_id') != receipt['run_id']
            or manifest.get('nomination_mode') != config['nomination_mode']
            or manifest.get('max_provider_requests') != config['budgets']['max_provider_requests']
            or manifest.get('decision_sha256') != config['runtime_s0_sha256']
            or manifest.get('history_sha256') != config['history_sha256']
            or manifest.get('report_sha256') != receipt['run_report_sha256']):
        raise ValueError('Run provenance mismatch')
    fm = read(frozen/'FREEZE_MANIFEST.json')
    matches(frozen/'FREEZE_MANIFEST.json', config['frozen_manifest_sha256'], 'frozen manifest')
    matches(frozen/'S0_ATOMIC_REVIEWER_CONFIRMED.json', fm['s0_sha256'], 'frozen S0')
    if fm['s0_sha256'] != config['frozen_s0_sha256']:
        raise ValueError('Frozen S0 changed')
    for name, value in fm['reference_sha256'].items():
        matches(frozen/'reference'/name, value, 'frozen reference '+name)
    for relative, key in [('PREP_MANIFEST.json', 'original_api_prep_sha256'),
                          ('API_CONFIG.json', 'original_api_config_sha256'),
                          ('run/report.json', 'original_api_report_sha256'),
                          ('score/metrics.json', 'original_api_score_sha256')]:
        matches(source/relative, config[key], 'original API '+relative)
    matches(offline/'score'/'metrics.json', config['original_offline_score_sha256'], 'offline baseline')
    old_api, old_offline = read(source/'score'/'metrics.json'), read(offline/'score'/'metrics.json')
    if old_api.get('run_sha256') != config['original_api_report_sha256']:
        raise ValueError('Original API metrics do not match recorded report')
    previous43 = previous_metrics(args.previous_v43.resolve(), config.get('previous_v43'), 43, fm['s0_sha256'])
    previous44 = previous_metrics(args.previous_v44.resolve(), config.get('previous_v44'), 44, fm['s0_sha256'])
    previous45 = previous_metrics(args.previous_v45.resolve(), config.get('previous_v45'), 45, fm['s0_sha256'])
    previous46 = previous_metrics(args.previous_v46.resolve(), config.get('previous_v46'), 46, fm['s0_sha256'])
    previous47 = previous_metrics(args.previous_v47.resolve(), config.get('previous_v47'), 47, fm['s0_sha256'])
    previous48 = previous_metrics(args.previous_v48.resolve(), config.get('previous_v48'), 48, fm['s0_sha256'])
    previous42 = (previous_metrics(args.previous_v42.resolve(), config.get('previous_v42'), 42, fm['s0_sha256'])
                  if args.previous_v42 is not None else None)
    # Include the checkpoint attestation in completed-run provenance before any
    # private labels are interpreted. The exact-triple scorer remains unchanged.
    verified_members(ev)
    if (ev/'score').exists():
        # The bundler above verifies the committed score receipt, output hashes,
        # report, code and frozen-reference identity. Reuse is read-only and all
        # original comparator/reference hashes were rechecked before returning.
        summary = read(ev/'score'/'metrics.json')
        print(json.dumps({'status': 'V49_EXISTING_SCORE_VERIFIED_AND_REUSED_NO_API_CALLED',
                          'verified_links': summary['verified_evidence_links'],
                          'comparison': summary['comparison'], 'output': str(ev/'score')}, indent=2))
        return
    # Claim one scoring attempt before label interpretation. A competing or
    # interrupted attempt cannot create or overwrite an existing result.
    with (ev/'SCORE_ATTEMPT.json').open('x', encoding='utf-8') as claim:
        json.dump({'status': 'V49_SCORE_ATTEMPT_STARTED', 'run_report_sha256': receipt['run_report_sha256']}, claim)
        claim.write('\n')
    # Only here are private label rows interpreted, after the completed run checks.
    with (frozen/'reference'/HUNK_FILE).open(encoding='utf-8-sig', newline='') as stream:
        labels = list(csv.DictReader(stream))
    if len(labels) != 30 or len({r['hunk_id'] for r in labels}) != 30:
        raise ValueError('Expected exactly 30 distinct hunk labels')
    if any(r['relation_candidate'] not in KNOWN for r in labels):
        raise ValueError('Unexpected reference relation')
    report = read(ev/'run'/'report.json')
    summary = {
        'status': 'V49_DEVELOPMENT_ONLY_POST_RUN_REFERENCE_COMPARISON',
        'v49_code_sha256': config['v49_python_sha256'], 'frozen_s0_sha256': fm['s0_sha256'],
        'v49_run_report_sha256': receipt['run_report_sha256'], 'models': receipt['model'],
        'investigation_profile': PROFILE, 'nominal_budgets': config['budgets'],
        'nomination_mode': config['nomination_mode'],
        'parent_v44_models': config['parent_v44_models'], 'parent_v45_models': config['parent_v45_models'],
        'parent_v46_models': config['parent_v46_models'], 'parent_v47_models': config['parent_v47_models'],
        'parent_v48_models': config['parent_v48_models'], 'semantic_phase_config': SEMANTIC_PHASE_CONFIG,
        'policy_change_note': POLICY_CHANGE_NOTE, 'model_change_note': MODEL_CHANGE_NOTE,
        'comparison_note': COMPARISON_NOTE, 'budget_usage': report.get('budget_usage'),
        'verified_evidence_links': len(report.get('verified_evidence', [])),
        'verification_status': (report.get('verification') or {}).get('status'),
        'results': {}, 'comparison': {},
        'warnings': ['NOT held-out: the reference was examined during development.', COMPARISON_NOTE, MODEL_CHANGE_NOTE, POLICY_CHANGE_NOTE,
                     'The exact-triple scorer is unchanged; no architecture-outcome gold is available.',
                     'Historical replay remains uncertified; model snapshots are not verified.'],
    }
    errors = []
    for scope in EVAL_SCOPES:
        result, rows = evaluate(labels, report, scope)
        result['limitations'] = [v for v in result['limitations'] if 'offline mode' not in v]
        result['limitations'].extend(['v4.9 development examples, not independent held-out evaluation',
                                      'different profile and provider-call/token accounting'])
        summary['results'][scope] = result
        comparators = {'offline_v41_f1': old_offline['results'][scope], 'api_v41_f1': old_api['results'][scope],
                       'api_v43_dev_f1': previous43['results'][scope], 'api_v44_dev_f1': previous44['results'][scope],
                       'api_v45_dev_f1': previous45['results'][scope], 'api_v46_dev_f1': previous46['results'][scope],
                       'api_v47_dev_f1': previous47['results'][scope], 'api_v48_dev_f1': previous48['results'][scope]}
        if previous42 is not None:
            comparators['api_v42_dev_f1'] = previous42['results'][scope]
        for other in comparators.values():
            if (other['gold_positive_exact_triples'] != result['gold_positive_exact_triples']
                    or other['evaluated_hunks'] != result['evaluated_hunks']):
                raise ValueError('Comparison reference population changed')
        comparison = {key: value['f1'] for key, value in comparators.items()}
        comparison.update({'api_v49_dev_f1': result['f1'],
                           'delta_v49_minus_api_v41': round(result['f1'] - comparators['api_v41_f1']['f1'], 6),
                           'delta_v49_minus_v43': round(result['f1'] - comparators['api_v43_dev_f1']['f1'], 6),
                           'delta_v49_minus_v44': round(result['f1'] - comparators['api_v44_dev_f1']['f1'], 6),
                           'delta_v49_minus_v45': round(result['f1'] - comparators['api_v45_dev_f1']['f1'], 6),
                           'delta_v49_minus_v46': round(result['f1'] - comparators['api_v46_dev_f1']['f1'], 6),
                           'delta_v49_minus_v47': round(result['f1'] - comparators['api_v47_dev_f1']['f1'], 6),
                           'delta_v49_minus_v48': round(result['f1'] - comparators['api_v48_dev_f1']['f1'], 6),
                           'note': COMPARISON_NOTE})
        if previous42 is not None:
            comparison['delta_v49_minus_v42'] = round(result['f1'] - comparators['api_v42_dev_f1']['f1'], 6)
        summary['comparison'][scope] = comparison
        errors.extend(rows)
    staging = Path(tempfile.mkdtemp(prefix='.v49-score-staging-', dir=ev))
    try:
        save(staging/'metrics.json', summary)
        with (staging/'link_errors.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['scope', 'verdict', 'hunk_id', 'atomic_s0_id', 'relation',
                                                       'reference_hunk_relation', 'temporal_basis'])
            writer.writeheader()
            writer.writerows(errors)
        save(staging/'SCORE_RECEIPT.json', {
            'status': 'V49_SCORE_COMMITTED', 'run_report_sha256': receipt['run_report_sha256'],
            'core_sha256': config['v49_python_sha256'], 'frozen_manifest_sha256': config['frozen_manifest_sha256'],
            'metrics_sha256': digest(staging/'metrics.json'), 'link_errors_sha256': digest(staging/'link_errors.csv')})
        if (ev/'score').exists():
            raise FileExistsError('Score destination appeared during scoring; preserve both attempts')
        os.rename(staging, ev/'score')
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    print(json.dumps({'status': summary['status'], 'verified_links': summary['verified_evidence_links'],
                      'comparison': summary['comparison'], 'output': str(ev/'score')}, indent=2))


if __name__ == '__main__':
    main()
