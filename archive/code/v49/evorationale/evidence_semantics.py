"""Deterministic evidence *screening* for directly stated architectural facts.

An eligibility/provenance gate is not semantic entailment.  This module instead
performs a deliberately high-precision, fallible screen used by the offline
reference linker and as an additional safety gate before the optional semantic
LLM judge. It must not be used as independently adjudicated research labels.

Important: the quote, not the surrounding PR/title/tags, must carry the
relevant facts.  A modification to a file does not establish an architectural
feature; a generic networking change does not substantiate an AVNM decision.
"""
from __future__ import annotations

import re
from typing import Any

# Code identifiers, paths and product acronyms must be compared in the source
# quotation, not just in metadata or unrelated sections of a long PR.
_FILE = re.compile(r"\b[\w./-]+\.(?:json|ya?ml|java|py|ts|js|go|rs|xml|toml|md|sql|properties)\b", re.I)
_SYMBOL = re.compile(r"\b[a-z][a-z0-9]*[A-Z][A-Za-z0-9]*\b")
_ACRONYM = re.compile(r"\b[A-Z][A-Z0-9]{2,}\b")
_WORD = re.compile(r"[a-z0-9]+", re.I)
_STOP = {"the","for","and","with","from","into","that","this","using","added","add",
         "support","supports","supported","deployment","architecture","decision",
         "include","includes","change","changes","new","files","file","system",
         "project","related","updated","update","implement","implemented"}
_ACTION = re.compile(r"\b(?:add(?:s|ed|ing)?|introduc(?:e|es|ed|ing)|expos(?:e|es|ed|ing)|"
                     r"implement(?:s|ed|ing)?|integrat(?:e|es|ed|ing)|enabl(?:e|es|ed|ing)|"
                     r"deploy(?:s|ed|ing|ment)?|configur(?:e|es|ed|ing)|"
                     r"support(?:s|ed|ing)?|confirm(?:s|ed)?|"
                     r"pass(?:es|ed)?|meet(?:s|ing)?|present)\b", re.I)
_CHANGE_ONLY = re.compile(r"\b(?:modified|changed files|renamed|touched|updated file)\b", re.I)
_CONDITION = re.compile(r"\b(?:condition(?:s|al)?|conditional|when|if|guard(?:s|rails)?|dependsOn|dependencies|dependent)\b", re.I)
_MARKDOWN_LINK = re.compile(r"\[\[?\d+\]?\]\([^)]*\)")
# For prose-based design documents, factual descriptive statements such as
# 'PodStatus reports allocated resources' can be material evidence even when
# the passage contains no 'add' or 'implement' verb. This is a *screen* only;
# the independent semantic judge must still examine the relationship.
_FACT_ASSERTION = re.compile(
    r"\b(?:is|are|was|were|will|must|shall|should|can|cannot|"
    r"represents?|denotes?|reports?|records?|tracks?|holds?|"
    r"remains?|includes?|contains?|requires?|allows?|permits?|"
    r"provides?|maintains?|excludes?|becomes?)\b", re.I)
_CONTEXT_ACRONYMS = {'KEP', 'RFC', 'ADR'}


def _words(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text) if len(w) >= 3 and w.lower() not in _STOP}


def _contains(source: str, needle: str) -> bool:
    # Case-insensitive exact token matching, allowing directory prefixes in paths.
    term = needle.lower()
    if '/' in term or '.' in term:
        return term in source.lower()
    return bool(re.search(r"(?<![a-z0-9_])" + re.escape(term) + r"(?![a-z0-9_])", source.lower()))


def _technical_tokens(element: dict[str, Any]) -> tuple[list[str],list[str],list[str]]:
    """Return code paths, camel-case symbols, and acronyms from element TEXT.

    Keywords are treated as search hints, not mandatory truth conditions:
    a tag added by a researcher cannot make an otherwise unrelated sentence
    relevant. Paths like `eslzArm/eslzArm.json` match `eslzArm.json`.
    """
    text = element["text"]
    filenames = list(dict.fromkeys(_FILE.findall(text)))
    symbols = [x for x in dict.fromkeys(_SYMBOL.findall(text))
               if not any(x.lower() in path.lower() for path in filenames)]
    acronyms = [x for x in dict.fromkeys(_ACRONYM.findall(text))
                if not any(x.lower() in sym.lower() for sym in symbols)]
    return filenames, symbols, acronyms


def direct_relevance(element: dict[str, Any], quote: str, relation: str, *,
                     allow_descriptive: bool = False) -> tuple[bool, str]:
    """Screen element-target specificity; a success is NOT scientific proof.

    Implementation/support links require all documented code symbols/paths.
    For less formal rationale (e.g. a workload assumption), require at least
    two distinctive anchors or a substantial lexical overlap. Opposing evidence
    receives a less rigid screen because changes may indirectly affect a prior
    rationale, but a completely unrelated quote is never accepted.
    """
    if not isinstance(quote,str) or not quote.strip():
        return False, "empty_evidence_quote"
    body = quote.lower()
    etype = element.get("element_type", "")
    files,symbols,acronyms = _technical_tokens(element)
    text_terms = _words(element["text"])
    quote_terms = _words(quote)
    overlap = text_terms & quote_terms

    if relation == 'supports':
        # Positive claims must be evidenced by the stated feature, not just
        # a touched file or a generic capability near it in a large PR.
        for file in files:
            if not _contains(quote,file):
                return False, 'missing_exact_file_anchor:' + file
        for symbol in symbols:
            if not _contains(quote,symbol):
                return False, 'missing_exact_code_symbol:' + symbol
        # A decision can have a subject acronym and a context acronym (e.g.
        # AVNM within ESLZ). The first is obligatory; requiring every context
        # abbreviation causes false negatives on accurate excerpts.
        subject_acronyms = ([ac for ac in acronyms if ac not in _CONTEXT_ACRONYMS]
                            if allow_descriptive else acronyms)
        if subject_acronyms and not _contains(quote,subject_acronyms[0]):
            return False, 'missing_decision_subject:' + subject_acronyms[0]
        # An item about implementation *must* contain substantive facts.
        if etype in {'implementation_scope','constraints_dependencies'}:
            if not _ACTION.search(quote) and not (allow_descriptive and _FACT_ASSERTION.search(quote)
                                             and len(overlap) >= 3):
                return False, 'no_substantive_implementation_assertion'
            # Generic 'support' in a commit title plus touched-file metadata
            # is insufficient to prove a parameter or condition is present.
            if (_CHANGE_ONLY.search(quote) and 'changed files' in body and
                    not re.search(r'\b(?:parameter|checkbox|condition|dependsOn|\bbool\b)\b',quote,re.I)):
                return False, 'file_change_metadata_not_implementation_evidence'
            if ('condition' in element['text'].lower() or 'dependencies' in element['text'].lower()) and not _CONDITION.search(quote):
                return False,'missing_conditional_or_dependency_claim'
            # A code path + acronym alone is not proof of an additional aspect.
            if len(overlap) < 2 and not (files or symbols):
                return False,'insufficient_atomic_element_specificity'
        else:
            if not _ACTION.search(quote) and not (allow_descriptive and _FACT_ASSERTION.search(quote)
                                             and len(overlap) >= 3):
                return False,'no_explicit_positive_evidence'
            if len(overlap) < 2:
                return False,'insufficient_goal_or_rationale_specificity'
        return True, 'DIRECT_ELEMENT_ANCHORS_PRESENT_REVIEW_REQUIRED'

    if etype == 'implementation_scope' and files and not any(_contains(quote,x) for x in files):
        # A regression can describe behavior without the exact file name:
        # allow this only with multiple substantive, non-file words in common.
        if len(overlap) < 3:
            return False,'insufficient_implementation_specificity'
    # An indirect change may refer to the archived evidence type (e.g. a new
    # 'database benchmark' superseding a latency benchmark), not repeat every
    # word of the old statement. Approved S0 keywords are search hints only;
    # multiple DISTINCT hits are still required.
    if len(overlap) < 2 and len((text_terms | _words(' '.join(element.get('keywords',[])))) & quote_terms) < 2:
        return False,'insufficient_rationale_specificity'
    return True,'ADVERSE_EVIDENCE_SCREEN_REVIEW_REQUIRED'


def evidence_spans(content: str, max_chars: int = 650, *,
                   include_multiline: bool = True) -> list[str]:
    """Short contiguous, verbatim text spans; no rewriting and no fabrications.

    Documents are split into paragraphs, bullet lines and sentences, including
    adjacent pairs of sentences for facts explained across sentence boundaries.
    Large text never becomes a single 'supporting quote'. Returned substrings
    are checked verbatim against canonical artifact bytes by EvidenceVerifier.
    """
    if not content:
        return []
    candidates=[]
    # Some markdown lines contain enormous autogenerated diffhunk references.
    for paragraph in re.split(r'\n\s*\n',content):
        if not paragraph.strip():
            continue
        parts=[]
        for line in paragraph.splitlines():
            if not line.strip() or line.strip().startswith('<!--'):
                continue
            if len(line)>max_chars:
                # Raw prefix BEFORE link references: still an exact substring.
                cut=re.split(r'\s+\[\[?\d+',line,maxsplit=1)[0]
                if 0<len(cut)<=max_chars:
                    parts.append(cut.strip())
                else:
                    # Split a long line at punctuation/semantic delimiters.
                    parts += [x.strip() for x in re.split(r'(?<=[.!?;])\s+(?=[A-Za-z*`])',line)
                              if 0<len(x.strip())<=max_chars]
            else:
                parts.append(line.strip())
        if not parts:
            continue
        for chunk in parts:
            sentences=[x.strip() for x in re.split(r'(?<=[.!?])\s+(?=[A-Z*])',chunk) if x.strip()]
            # Preserve exact source wording and exact whitespace for citation.
            for sentence in sentences:
                if sentence and len(sentence)<=max_chars and sentence in content:
                    candidates.append(sentence)
            for a,b in zip(sentences,sentences[1:]):
                # Only combine text that was contiguous in the original.
                start=content.find(a)
                if start>=0:
                    j=content.find(b,start+len(a))
                    if j>=0:
                        combined=content[start:j+len(b)]
                        if len(combined)<=max_chars:
                            candidates.append(combined)
        # Do NOT combine independent Markdown bullets: that can falsely merge
        # an AVNM change and unrelated deployment conditions into one claim.
        # Sentence-pairs within one prose line remain available above.
    # An added/changed architectural fact may wrap across multiple adjacent
    # lines in a Git patch or prose paragraph. Preserve the precise newline
    # and +/- prefixes; never synthesize words or bridge independent bullets.
    for paragraph in (re.split(r'\n\s*\n', content) if include_multiline else []):
        lines = paragraph.splitlines(keepends=True)
        if len(lines) < 2:
            continue
        for start in range(len(lines)):
            first = lines[start].strip()
            if not first or first.startswith(('@@', '+++', '---', '<!--')):
                continue
            for width in (2, 3, 4):
                if start + width > len(lines):
                    break
                group = lines[start:start + width]
                trimmed = [line.strip() for line in group]
                if any(not x or x in ('+', '-') or x.startswith(('@@', '+++', '---'))
                       for x in trimmed):
                    break
                # No joining separate ordinary Markdown bullet items.
                if sum(bool(re.match(r'^\s*[*-]\s+', x)) for x in group) > 1:
                    break
                # Source-context mixed additions and removals are still
                # verifiable, but a quote needs at least one changed line.
                candidate = ''.join(group).strip()
                if not (30 <= len(candidate) <= max_chars and candidate in content):
                    continue
                candidates.append(candidate)
    # Title-like, simple whole short content is valid (Redis demo).
    if len(content.strip())<=max_chars and not re.search(r"(?m)^\s*[-*]\s+.*\n\s*[-*]\s+",content):
        candidates.insert(0,content.strip())
    return list(dict.fromkeys(q for q in candidates if q and q in content))
