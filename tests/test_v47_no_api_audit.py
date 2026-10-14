"""Validate the new profile's real source audit separately from transport fixtures."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from test_v46_no_api_audit import source, prepared, MODELS, BUDGETS

TOOL = Path(__file__).resolve().parents[1]/'development_tools/audit_v47_no_api.py'
spec = importlib.util.spec_from_file_location('audit_v47_fixture', TOOL)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_grounded_source_audit_uses_one_classifier_per_batch(approved_state):
    history = [source(approved_state), source(approved_state, 'second', 'b'*40)]
    unchanged = deepcopy((approved_state, history))
    result = audit.audit_sources(approved_state, history, MODELS, BUDGETS)
    assert (approved_state, history) == unchanged
    assert result['provider_calls'] == 0 and result['mock_transport_calls'] == 2
    assert result['mock_nomination_requests'] == 0
    assert result['semantic_result_available'] is False and result['gold_labels_read'] is False
    assert all(r['max_output_tokens'] == BUDGETS['max_output_tokens']
               for r in result['request_envelopes'])


def test_grounded_source_audit_honestly_reports_unaffordable_estimate(approved_state):
    result = audit.audit_sources(approved_state, [source(approved_state)], MODELS,
                                 {**BUDGETS, 'max_input_tokens':1})
    assert not result['scenario_within_nominal_estimate_budget']
    assert result['first_unaffordable_envelope_in_scenario']['stage'] == 'judge'
    assert result['mock_transport_calls'] == 1


def test_grounded_audit_forbids_extra_nomination_phase(approved_state):
    with pytest.raises(ValueError, match='requires nomination mode none'):
        audit.audit_sources(approved_state, [source(approved_state)], MODELS, BUDGETS,
                            nomination_mode='model')


@pytest.mark.parametrize('changed', [{}, {'nomination_mode':'model'},
                                    {'investigation_profile':'event-evidence'},
                                    {'kind':'DEVELOPMENT_ONLY_V47_EVENT_EVIDENCE_COMPARISON'}])
def test_prepared_grounded_audit_cli_validates_profile_identity(tmp_path, approved_state, changed):
    evaluation = prepared(tmp_path, approved_state)
    path = evaluation/'DEV_PREP_MANIFEST.json'
    config = json.loads(path.read_text())
    config.update(kind='DEVELOPMENT_ONLY_V47_EVENT_GROUNDED_COMPARISON',
                  investigation_profile='event-grounded', nomination_mode='none')
    config.update(changed)
    path.write_text(json.dumps(config))
    result = subprocess.run([sys.executable, str(TOOL), '--evaluation', str(evaluation)],
                            capture_output=True, text=True)
    if changed:
        assert result.returncode != 0
    else:
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report['investigation_profile']=='event-grounded' and report['provider_calls']==0
