"""Generic baseline identity/selection checks; no reference labels or transport."""
from copy import deepcopy
import hashlib

import pytest

from baseline_context import build_baseline_context, ROLE, SELECTION_METHOD

COMMIT = '1' * 40
URL = 'https://github.com/sample/project/blob/' + COMMIT + '/design/README.md'


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def fixture(raw=None, anchors=('L10-L12', 'L20-L21')):
    raw = raw if raw is not None else ''.join(f'line {i}: café\n' for i in range(1, 41)).encode()
    state = {'baseline_git_commit': COMMIT, 'baseline_readme_git_blob_sha1': blob(raw),
             'goals': [{'id': 'TARGET_A', 'text': 'A neutral goal.', 'source': URL + '#' + anchors[0]}],
             'requirements': [{'id': 'TARGET_B', 'text': 'A neutral requirement.', 'source': URL + '#' + anchors[1]}]}
    return state, raw


def selected(result):
    return [line for excerpt in result['excerpts'] for line in excerpt['lines']]


def test_all_targets_plus_qualifier_margins_are_merged_without_mutation():
    state, raw = fixture(anchors=('L10-L12', 'L20-L21'))
    before = deepcopy(state)
    result = build_baseline_context(state, raw)
    assert state == before
    assert result['selection_method'] == SELECTION_METHOD and result['margin_lines'] == 4
    assert [(e['start_line'], e['end_line']) for e in result['excerpts']] == [(6, 25)]
    assert [line['line_number'] for line in selected(result)] == list(range(6, 26))
    assert len({line['handle'] for line in selected(result)}) == result['selected_line_count'] == 20
    assert selected(result)[0]['handle'] == 'B:L0006'
    assert selected(result)[0]['text'] == 'line 6: café'
    assert {r['element_id'] for r in result['target_ranges']} == {'TARGET_A', 'TARGET_B'}
    assert result['raw_sha256'] == hashlib.sha256(raw).hexdigest() and result['git_blob_sha1'] == blob(raw)
    assert result['fresh_post_s0_evidence'] is result['semantic_assessment_performed'] is False
    assert result['incomplete_whole_source'] and result['interpretation_epistemic_status'] == 'MODEL_ASSESSED'
    assert all(r['role'] == ROLE and not r['handle'].startswith('A') for r in selected(result))
    assert 'A neutral goal.' not in str(result)  # No unrelated state or labels copied.


def test_utf8_and_crlf_exact_git_identity_and_line_numbers():
    raw = ''.join(f'α line {i}\r\n' for i in range(1, 41)).encode('utf-8')
    state, _ = fixture(raw, anchors=('L1', 'L40-L40'))
    result = build_baseline_context(state, raw)
    assert result['whole_source_line_count'] == 40
    assert [(e['start_line'], e['end_line']) for e in result['excerpts']] == [(1, 5), (36, 40)]
    assert selected(result)[0]['text'] == 'α line 1'
    with pytest.raises(ValueError, match='Git blob'):
        build_baseline_context(state, raw.replace(b'\r\n', b'\n'))


def test_unicode_separator_is_not_a_physical_source_line_break():
    raw = ('line1\u2028continuation\n' + ''.join(f'line{i}\n' for i in range(2, 41))).encode()
    state, _ = fixture(raw, anchors=('L1', 'L40'))
    result = build_baseline_context(state, raw)
    assert result['whole_source_line_count'] == 40 and selected(result)[0]['text'] == 'line1\u2028continuation'


@pytest.mark.parametrize('source', [URL.replace(COMMIT, '2'*40) + '#L10-L12',
    'http://github.com/sample/project/blob/'+COMMIT+'/design/README.md#L10-L12',
    URL.replace('github.com', 'example.com')+'#L10-L12', URL+'?q=other#L10-L12',
    URL.replace('/README.md', '/policy.md')+'#L10-L12', URL+'#L0-L10', URL+'#L12-L10',
    URL+'#L10-L99', URL, URL+'#unknown', URL.replace('/design/', '/design/../')+'#L10-L12'])
def test_wrong_commit_url_file_or_range_fails_closed(source):
    state, raw = fixture(); state['goals'][0]['source'] = source
    with pytest.raises(ValueError): build_baseline_context(state, raw)


def test_mixed_readme_source_files_fail_even_if_commit_matches():
    state, raw = fixture(); state['requirements'][0]['source'] = URL.replace('/design/', '/another/')+'#L20-L21'
    with pytest.raises(ValueError, match='mixed'): build_baseline_context(state, raw)


@pytest.mark.parametrize('pin', ['baseline_git_commit', 'baseline_readme_git_blob_sha1'])
def test_malformed_pin_fails(pin):
    state, raw = fixture(); state[pin] = 'not-a-pin'
    with pytest.raises(ValueError, match='pin'): build_baseline_context(state, raw)


def test_over_cap_never_silently_drops_targets():
    raw = ''.join(f'line{i}\n' for i in range(1, 601)).encode()
    state, _ = fixture(raw, anchors=('L1-L220', 'L280-L510'))
    with pytest.raises(ValueError, match='line cap'): build_baseline_context(state, raw)


def test_outbound_screening_keeps_positions_and_raw_identity():
    lines = [f'line{i}' for i in range(1, 41)]
    lines[9] = 'OPENAI_API_KEY=sk-' + 'a'*60
    raw = ('\n'.join(lines)+'\n').encode(); state, _ = fixture(raw)
    result = build_baseline_context(state, raw)
    line10 = next(r for r in selected(result) if r['line_number'] == 10)
    assert line10['screened'] and 'sk-'+'a'*60 not in line10['text']
    assert line10['handle'] == 'B:L0010' and result['raw_sha256'] == hashlib.sha256(raw).hexdigest()
    assert result['screened_selected_line_count'] >= 1


def test_empty_or_duplicate_targets_are_rejected():
    state, raw = fixture(); state['goals'] = []; state['requirements'] = []
    with pytest.raises(ValueError, match='No fixed targets'): build_baseline_context(state, raw)
    state, raw = fixture(); state['requirements'][0]['id'] = 'TARGET_A'
    with pytest.raises(ValueError, match='duplicate'): build_baseline_context(state, raw)


def test_cross_line_protected_value_is_screened_using_whole_source():
    lines = [f'line{i}' for i in range(1, 41)]
    lines[8] = 'password='
    lines[9] = 'opaque_private_value_without_a_token_prefix'
    raw = ('\n'.join(lines)+'\n').encode(); state, _ = fixture(raw)
    result = build_baseline_context(state, raw)
    protected = [r for r in selected(result) if r['line_number'] in {9, 10}]
    assert all(r['screened'] and r['text'] == '[BASELINE_SOURCE_LINE_SCREENED]' for r in protected)
    assert 'opaque_private_value_without_a_token_prefix' not in str(result)
    assert result['raw_sha256'] == hashlib.sha256(raw).hexdigest()


def test_declared_state_repository_must_match_every_baseline_url():
    state, raw = fixture(); state['repository'] = 'sample/project'
    assert build_baseline_context(state, raw)['repository'] == 'sample/project'
    state['repository'] = 'other/project'
    with pytest.raises(ValueError, match='repository differs'):
        build_baseline_context(state, raw)
