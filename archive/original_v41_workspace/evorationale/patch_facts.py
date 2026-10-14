"""Narrow deterministic code-fact screen for *captured unified PR diffs*.

The input format is `pull_request_diff_excerpt` produced by the companion
collector. The source-path header is collector metadata, not verbatim code.
We require matching ADDED lines for each atomic implementation claim, and
reject other elements rather than pretending a file change proves rationale.
This screen cannot prove correctness, deployment, or historical availability.
"""
from __future__ import annotations

import re
from typing import Any

PATCH_SOURCE_TYPE = 'pull_request_diff_excerpt'


def added_lines(quote: str) -> list[str]:
    return [line[1:].strip() for line in quote.splitlines()
            if line.startswith('+') and not line.startswith('+++')]


def check_patch_fact(element:dict[str,Any], artifact:dict[str,Any],
                     quote:str, relation:str) -> tuple[bool,str]:
    if artifact.get('source_type') != PATCH_SOURCE_TYPE:
        return False,'not_a_verified_patch_excerpt'
    if relation != 'supports':
        return False,'diff_does_not_directly_establish_adverse_relation'
    if element.get('element_type') not in {'implementation_scope','constraints_dependencies'}:
        return False,'code_diff_does_not_prove_goal_or_rationale'
    meta=artifact.get('metadata',{})
    if not isinstance(meta,dict):
        return False,'invalid_diff_metadata'
    path=meta.get('file_path','')
    if not isinstance(path,str) or not path.startswith('eslzArm/'):
        return False,'unverified_diff_file_path'
    if path not in quote:
        return False,'diff_quote_missing_source_path'
    if not isinstance(quote,str) or len(quote)>650:
        return False,'diff_quote_too_long'
    lines=added_lines(quote)
    if not lines:
        return False,'no_added_code_lines'
    added='\n'.join(lines)
    lowtext=element['text'].lower()
    pathlower=path.lower()

    # A parameter *definition*, not any mention of a parameter nor file name.
    if 'deployavnm' in lowtext and 'parameter' in lowtext:
        if not pathlower.endswith('/eslzarm.json'):
            return False,'parameter_in_wrong_file'
        defined=bool(re.search(r'"deployAVNM"\s*:\s*\{',added))
        typed=bool(re.search(r'"type"\s*:\s*"bool"',added,re.I))
        return (defined and typed,'ADDED_BOOLEAN_PARAMETER_DEFINITION' if defined and typed
                else 'no_added_boolean_deployAVNM_definition')

    # The portal checkbox is a concrete Create UI Definition control.
    if 'checkbox' in lowtext or ('eslz-portal.json' in lowtext and 'avnm' in lowtext):
        if not pathlower.endswith('/eslz-portal.json'):
            return False,'checkbox_in_wrong_file'
        name=bool(re.search(r'"name"\s*:\s*"deployAVNM"',added))
        widget=bool(re.search(r'"type"\s*:\s*"Microsoft\.Common\.CheckBox"',added,re.I))
        return (name and widget,'ADDED_PORTAL_CHECKBOX_CONTROL' if name and widget
                else 'no_added_portal_checkbox_definition')

    # Only a *new conditional expression* referencing AVNM, not generic
    # deployment-condition wording elsewhere in a PR.
    if 'condition' in lowtext:
        if not pathlower.endswith('/eslzarm.json'):
            return False,'condition_in_wrong_file'
        condition=bool(re.search(r'"condition"\s*:\s*"[^"\n]*deployAVNM[^"\n]*"',added,re.I))
        return (condition,'ADDED_AVNM_DEPLOYMENT_GUARD' if condition
                else 'no_added_deployAVNM_condition')

    if 'dependenc' in lowtext or 'dependenc' in ' '.join(element.get('keywords',[])).lower():
        if not pathlower.endswith('/eslzarm.json'):
            return False,'dependency_in_wrong_file'
        has_dep=bool(re.search(r'"dependsOn"\s*:',added,re.I))
        has_avnm_ref=bool(re.search(r'(?i)(?:avnmConnectivityHubDeploymentName|avnmPolicyDeploymentName|avnmLiteConnectivityHubDeploymentName)',added))
        return (has_dep and has_avnm_ref,'ADDED_AVNM_DEPENDENCY_EDGE' if has_dep and has_avnm_ref
                else 'no_added_AVNM_dependency_edge')

    return False,'patch_element_not_covered_by_atomic_code_screen'
