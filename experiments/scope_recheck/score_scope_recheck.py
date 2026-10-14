#!/usr/bin/env python3
"""Score a completed cached-primary experiment with the unchanged v4.9 scorer."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import tempfile
import zipfile

from _kit_common import EXPERIMENT, output_snapshot, read, sha, verified_parent, write_new


def bundle(evaluation, code_root, destination):
    members, hashes, receipt, _, _ = output_snapshot(evaluation, code_root)
    destination = Path(destination).resolve()
    manifest = {'status': 'SCOPE_RECHECK_DIAGNOSTICS_VERIFIED_NO_API_CALLED',
                'run_id': receipt['run_id'], 'experiment_kind': EXPERIMENT,
                'member_sha256': hashes}
    with destination.open('xb') as stream:
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name in sorted(members):
                archive.writestr(name, members[name])
            archive.writestr('DIAGNOSTIC_BUNDLE_MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code-root', required=True, type=Path)
    parser.add_argument('--evaluation', required=True, type=Path, help='New completed scope experiment')
    parser.add_argument('--frozen', required=True, type=Path, help='Original unchanged reference freeze')
    parser.add_argument('--source-evaluation', type=Path, help='Original completed v4.9 run if its folder moved')
    parser.add_argument('--output-bundle', type=Path, help='Optional NEW diagnostic ZIP')
    args = parser.parse_args()
    root, frozen = args.evaluation.resolve(), args.frozen.resolve()
    _, _, receipt, protocol, report = output_snapshot(root, args.code_root)
    if args.output_bundle is not None and args.output_bundle.exists():
        raise FileExistsError('Preserve existing scope diagnostic ZIP')
    from _score_core import EVAL_SCOPES, HUNK_FILE, KNOWN, digest, evaluate, matches
    source = verified_parent(args.code_root, args.source_evaluation or protocol['source_evaluation'])
    if source['hashes'] != protocol['source_member_sha256'] or source['run_id'] != protocol['source_run_id']:
        raise ValueError('Original primary/score provenance changed')
    freeze = read(frozen/'FREEZE_MANIFEST.json')
    matches(frozen/'FREEZE_MANIFEST.json', protocol['frozen_manifest_sha256'], 'original reference freeze')
    matches(frozen/'S0_ATOMIC_REVIEWER_CONFIRMED.json', protocol['frozen_s0_sha256'], 'original frozen S0')
    if freeze['s0_sha256'] != protocol['frozen_s0_sha256']:
        raise ValueError('Reference S0 identity changed')
    for name, expected in freeze['reference_sha256'].items():
        matches(frozen/'reference'/name, expected, 'original frozen reference ' + name)
    if (root/'score').exists():
        metrics = read(root/'score/metrics.json')
        if args.output_bundle is not None:
            bundle(root, args.code_root, args.output_bundle)
        print(json.dumps({'status': 'EXISTING_SCOPE_SCORE_VERIFIED_NO_API_CALLED',
                          'results': metrics['results'], 'output': str(root/'score'),
                          'diagnostic_zip': str(args.output_bundle) if args.output_bundle else None}, indent=2))
        return
    if (root/'SCORE_ATTEMPT.json').exists():
        raise FileExistsError('Preserve interrupted scope score attempt; inspect before retrying')
    write_new(root/'SCORE_ATTEMPT.json', {'status': 'SCOPE_SCORE_ATTEMPT_STARTED',
        'run_report_sha256': receipt['run_report_sha256'],
        'frozen_manifest_sha256': protocol['frozen_manifest_sha256']})
    # Reference row interpretation happens only after a completed real run and
    # all source/experiment/freeze checks. No row is ever passed to a model.
    with (frozen/'reference'/HUNK_FILE).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 30 or len({r['hunk_id'] for r in rows}) != 30 or any(r['relation_candidate'] not in KNOWN for r in rows):
        raise ValueError('Expected the unchanged 30-hunk frozen reference')
    previous = json.loads(source['members']['score/metrics.json'])
    results, errors, comparison = {}, [], {}
    for scope in EVAL_SCOPES:
        results[scope], scope_errors = evaluate(rows, report, scope)
        errors.extend(scope_errors)
        old = previous['results'][scope]
        if results[scope]['gold_positive_exact_triples'] != old['gold_positive_exact_triples']:
            raise ValueError('Frozen scoring denominator changed')
        comparison[scope] = {'v49_full_run_f1': old['f1'], 'cached_scope_recheck_f1': results[scope]['f1'],
            'delta_recheck_minus_v49': round(results[scope]['f1'] - old['f1'], 6),
            'note': 'Same cached primary predictions; changed critic. This is not a fresh full-pipeline or held-out evaluation.'}
    metrics = {'status': 'SCOPE_RECHECK_DEVELOPMENT_POST_RUN_REFERENCE_COMPARISON',
        'experiment_kind': EXPERIMENT, 'run_id': receipt['run_id'],
        'run_report_sha256': receipt['run_report_sha256'], 'source_run_id': protocol['source_run_id'],
        'toolkit_sha256': protocol['toolkit_sha256'], 'frozen_manifest_sha256': protocol['frozen_manifest_sha256'],
        'frozen_s0_sha256': protocol['frozen_s0_sha256'], 'results': results, 'comparison': comparison,
        'new_checker_budget_usage': report['budget_usage'], 'cached_primary_cost_is_not_zero': True,
        'new_primary_api_requests': 0,
        'limitations': ['Post-run development comparison; the reference has been examined during development.',
            'Cached v49 proposals constrain recall; an omitted primary relation cannot be recovered here.',
            'Report original classification cost when comparing end-to-end performance.',
            'Matching opaque model IDs do not certify immutable provider snapshots.',
            'No architecture-outcome Gold or held-out generalization is established.']}
    with tempfile.TemporaryDirectory(prefix='.scope-score-stage-', dir=root) as temporary:
        stage = Path(temporary)
        write_new(stage/'metrics.json', metrics)
        with (stage/'link_errors.csv').open('x', encoding='utf-8', newline='') as stream:
            columns = ['scope', 'verdict', 'hunk_id', 'atomic_s0_id', 'relation', 'reference_hunk_relation', 'temporal_basis']
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(errors)
        write_new(stage/'SCORE_RECEIPT.json', {'status': EXPERIMENT + '_SCORE_COMMITTED',
            'run_report_sha256': receipt['run_report_sha256'],
            'metrics_sha256': digest(stage/'metrics.json'), 'link_errors_sha256': digest(stage/'link_errors.csv')})
        stage.rename(root/'score')
    output_snapshot(root, args.code_root)
    if args.output_bundle is not None:
        bundle(root, args.code_root, args.output_bundle)
    print(json.dumps({'status': metrics['status'], 'results': results, 'comparison': comparison,
        'output': str(root/'score'), 'diagnostic_zip': str(args.output_bundle) if args.output_bundle else None}, indent=2))


if __name__ == '__main__':
    main()
