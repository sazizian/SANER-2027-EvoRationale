"""Pinned baseline excerpts for interpretation, never fresh post-baseline proof.

The caller pins and imports the historical EvoRationale code before calling this
module. Only fixed-state source URLs and exact public baseline bytes are used;
no reference labels, annotation notes, model transport or files are read here.
"""
from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
import re
from urllib.parse import unquote, urlsplit

MARGIN_LINES = 4
MAX_SELECTED_LINES = 450
ROLE = 'BASELINE_CONTEXT_ONLY_NOT_FRESH_POST_S0_PROOF'
SELECTION_METHOD = 'ALL_TARGET_SOURCE_RANGES_PLUS_4_LINES'
_HEX40 = re.compile(r'[0-9a-fA-F]{40}\Z')
_ANCHOR = re.compile(r'L([1-9][0-9]*)(?:-L([1-9][0-9]*))?\Z')


def _pin(value, name):
    if not isinstance(value, str) or _HEX40.fullmatch(value) is None:
        raise ValueError('Invalid baseline pin: ' + name)
    return value.lower()


def _source(url, commit):
    if not isinstance(url, str) or not url or url != url.strip():
        raise ValueError('Missing or invalid fixed-target source URL')
    try:
        parsed = urlsplit(url)
    except ValueError as exc:
        raise ValueError('Invalid fixed-target source URL') from exc
    if parsed.scheme != 'https' or parsed.netloc.lower() != 'github.com' or parsed.query:
        raise ValueError('Expected a pinned HTTPS GitHub baseline file URL')
    parts = unquote(parsed.path).split('/')
    if (len(parts) < 6 or parts[0] != '' or parts[3] != 'blob'
            or any(not part or part in {'.', '..'} or '\\' in part for part in parts[1:])):
        raise ValueError('Malformed baseline repository/file URL')
    if _pin(parts[4], 'source commit') != commit:
        raise ValueError('Fixed-target source commit differs from baseline commit')
    source_path = '/'.join(parts[5:])
    if PurePosixPath(source_path).name.lower() != 'readme.md':
        raise ValueError('Fixed target points outside the baseline README')
    anchor = _ANCHOR.fullmatch(parsed.fragment)
    if anchor is None:
        raise ValueError('Missing or invalid fixed-target baseline line range')
    start = int(anchor.group(1)); end = int(anchor.group(2) or anchor.group(1))
    if end < start:
        raise ValueError('Reversed fixed-target baseline line range')
    return '/'.join(parts[1:3]), source_path, start, end


def build_baseline_context(state, raw_bytes):
    """Validate pins, select *all* target ranges plus four-line margins and screen.

    Returned ``B:Lxxxx`` handles are deliberately outside the event ``A`` proof
    namespace. They identify interpretation context only. Git identity hashes
    cover the exact raw bytes before UTF-8 decoding or outbound screening.
    """
    if not isinstance(state, dict) or not isinstance(raw_bytes, bytes):
        raise ValueError('Expected a fixed state object and exact baseline bytes')
    commit = _pin(state.get('baseline_git_commit'), 'baseline_git_commit')
    expected_blob = _pin(state.get('baseline_readme_git_blob_sha1'), 'baseline_readme_git_blob_sha1')
    blob = hashlib.sha1(b'blob ' + str(len(raw_bytes)).encode('ascii') + b'\0' + raw_bytes).hexdigest()
    if blob != expected_blob:
        raise ValueError('Baseline README Git blob does not match its fixed-state pin')
    try:
        text = raw_bytes.decode('utf-8', errors='strict')
    except UnicodeDecodeError as exc:
        raise ValueError('Baseline README is not valid UTF-8') from exc
    if '\0' in text:
        raise ValueError('Baseline README contains binary NUL data')
    # GitHub source line numbers follow LF boundaries, rather than Python's
    # additional Unicode splitlines separators. CRLF strips only its terminator.
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    lines = [line[:-1] if line.endswith('\r') else line for line in lines]
    if not lines:
        raise ValueError('Empty baseline README')
    from evorationale.model import elements
    from evorationale.event_verification import _outbound, _overlaps_sensitive_source
    targets = elements(state)
    if not targets:
        raise ValueError('No fixed targets for baseline source selection')
    ranges, seen, identity = [], set(), None
    for target in targets:
        if not isinstance(target, dict) or not isinstance(target.get('id'), str) or not target['id'].strip() or target['id'] in seen:
            raise ValueError('Invalid or duplicate fixed-target identity')
        seen.add(target['id'])
        repository, source_path, start, end = _source(target.get('source'), commit)
        current_identity = (repository, source_path)
        if identity is not None and current_identity != identity:
            raise ValueError('Fixed targets point to mixed baseline source files')
        identity = current_identity
        if start < 1 or end > len(lines):
            raise ValueError('Fixed-target baseline source range is out of bounds')
        ranges.append({'element_id': target['id'], 'source_url': target['source'],
                       'anchor_start_line': start, 'anchor_end_line': end,
                       'selected_start_line': max(1, start - MARGIN_LINES),
                       'selected_end_line': min(len(lines), end + MARGIN_LINES)})
    if 'repository' in state and state['repository'] != identity[0]:
        raise ValueError('Fixed-state repository differs from the baseline source repository')
    merged = []
    for row in sorted(ranges, key=lambda r: (r['selected_start_line'], r['selected_end_line'])):
        start, end = row['selected_start_line'], row['selected_end_line']
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    count = sum(end - start + 1 for start, end in merged)
    if count > MAX_SELECTED_LINES:
        raise ValueError('All fixed-target baseline ranges exceed the line cap; no selective drop allowed')
    excerpts = []
    screened_count = 0
    for start, end in merged:
        selected = []
        for number in range(start, end + 1):
            original = lines[number - 1]
            # Full-source overlap screening also catches a credential prefix
            # on a preceding physical line. Preserve the position, not a
            # potentially sensitive continuation or an ambiguous duplicate.
            screened = ('[BASELINE_SOURCE_LINE_SCREENED]'
                        if _overlaps_sensitive_source(text, original) else _outbound(original))
            screened_count += screened != original
            selected.append({'handle': f'B:L{number:04d}', 'line_number': number,
                             'text': screened, 'role': ROLE,
                             'screened': screened != original})
        excerpts.append({'start_line': start, 'end_line': end, 'lines': selected})
    payload = {'role': ROLE, 'selection_method': SELECTION_METHOD,
        'repository': identity[0], 'source_path': identity[1], 'baseline_git_commit': commit,
        'git_blob_sha1': blob, 'raw_sha256': hashlib.sha256(raw_bytes).hexdigest(),
        'raw_byte_count': len(raw_bytes), 'whole_source_line_count': len(lines),
        'selected_line_count': count, 'screened_selected_line_count': screened_count,
        'margin_lines': MARGIN_LINES, 'maximum_selected_lines': MAX_SELECTED_LINES,
        'all_fixed_target_ranges_selected': True, 'target_ranges': ranges, 'excerpts': excerpts,
        'incomplete_whole_source': True, 'fresh_post_s0_evidence': False,
        'interpretation_epistemic_status': 'MODEL_ASSESSED',
        'semantic_assessment_performed': False,
        'identity_checks': 'EXACT_RAW_GIT_BLOB_PIN_AND_ALL_TARGET_COMMIT_FILE_LINE_RANGES',
        'limitations': ['Only all target-anchored excerpts and their four-line margins are provided, not the whole source.',
                       'Relevant qualifications outside these excerpts or on screened lines may be missing; do not infer source-wide absence.',
                       'Baseline context is interpretation data, not fresh post-S0 proof, deployment evidence or semantic certification.',
                       'Source identity is checked against the caller-provided fixed-state pins; no remote repository or signature is verified.']}
    # Metadata can contain URLs; screen the full outbound object too. Original
    # raw bytes and the caller's fixed state are never changed or returned.
    return _outbound(payload)
