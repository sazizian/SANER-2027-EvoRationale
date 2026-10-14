"""Human-review-only atomic decomposition of a documented AVNM pilot state.

This is an exploratory proposal, not a gold label or a new accepted decision.
Input authoritative S0 remains completely unchanged.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from .model import validate_state


def propose_azure_avnm_atomic_state(original: dict[str, Any]) -> dict[str, Any]:
    state = validate_state(original)
    if state['repository'] != 'Azure/Enterprise-Scale' or state['decision_id'] != 'GitHub-PR-1803':
        raise ValueError('This decomposition is scoped to the reviewed Azure AVNM #1803 pilot only')
    raw_i = state.get('implementation_scope', [])
    raw_c = state.get('constraints_dependencies', [])
    if len(raw_i) != 1 or raw_i[0]['id'] != 'I1' or len(raw_c) != 1 or raw_c[0]['id'] != 'C1':
        raise ValueError('Unexpected original rationale elements: stop for manual review')
    text = raw_i[0]['text'].lower()
    if not all(term in text for term in ('deployavnm', 'eslzarm.json', 'eslz-portal.json', 'checkbox', 'conditions')):
        raise ValueError('Original I1 does not match the reviewed composite statement')

    result = deepcopy(state)
    source_i = deepcopy(raw_i[0])
    source_c = deepcopy(raw_c[0])
    def component(parent: dict[str, Any], id: str, description: str, keywords: list[str]) -> dict[str, Any]:
        return {
            'id': id, 'text': description, 'source': parent['source'],
            'keywords': keywords, 'decomposed_from_id': parent['id'],
            'source_status': 'DRAFT_CANDIDATE_REQUIRES_ANCHOR_REVIEW',
        }
    result['implementation_scope'] = [
        component(source_i, 'I1a', 'Introduce deployAVNM as an ARM deployment parameter in eslzArm.json.',
                  ['deployAVNM', 'eslzArm.json', 'AVNM', 'parameter']),
        component(source_i, 'I1b', 'Expose an AVNM deployment checkbox in eslz-portal.json.',
                  ['AVNM', 'checkbox', 'eslz-portal.json', 'deployAVNM']),
        component(source_i, 'I1c', 'Integrate AVNM deployment conditions in eslzArm.json.',
                  ['AVNM', 'deployment', 'conditions', 'eslzArm.json']),
    ]
    result['constraints_dependencies'] = [
        component(source_c, 'C1a', 'Update AVNM-related deployment conditions.',
                  ['AVNM', 'deployment', 'conditions']),
        component(source_c, 'C1b', 'Update AVNM-related deployment dependencies.',
                  ['AVNM', 'deployment', 'dependencies']),
    ]
    result['central_element_ids'] = ['G1', 'I1a', 'I1b', 'I1c']
    result['composite_groups'] = [
        {'original_id': 'I1', 'member_ids': ['I1a', 'I1b', 'I1c']},
        {'original_id': 'C1', 'member_ids': ['C1a', 'C1b']},
    ]
    result['human_approved'] = False
    result['builder_status'] = 'EXPLORATORY_ATOMIC_DRAFT_HUMAN_APPROVAL_REQUIRED'
    result['research_label'] = 'EXPLORATORY_S0_REVISION_NOT_ORIGINAL_GOLD'
    result['original_episode_id'] = state['episode_id']
    result['episode_id'] = state['episode_id'] + '-atomic-exploratory'
    result['original_composite_elements'] = [source_i, source_c]
    source_bytes = json.dumps(state, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    result['derived_from_approved_s0_sha256'] = hashlib.sha256(source_bytes).hexdigest()
    result['review_instructions'] = (
        'Check every proposed atomic statement against the accepted PR #1803 at the decision time; '
        'remove unsupported clauses and document all corrections before explicit human approval. '
        'Do not present exploratory rerun as held-out evaluation.'
    )
    validate_state(result, require_approved=False)
    return result
