"""Repository segments with artifact-version provenance and bounded context.

Offline mode uses whitespace units and is explicitly approximate. With a pinned
*fast* BGE-M3 tokenizer, use exact offset mappings and reserve two positions
for tokenizer special tokens so every emitted segment stays within 1024 tokens.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class Segment:
    segment_id: str
    start: int
    end: int
    text: str
    parent_key: str


def segment_text(text: str, parent_key: str, max_tokens: int = 1024,
                 overlap: int = 128, tokenizer: Any = None) -> list[Segment]:
    if max_tokens <= overlap + (2 if tokenizer is not None else 0) or overlap < 0:
        raise ValueError("max_tokens must exceed overlap (+ 2 reserved specials for exact tokenization)")
    if tokenizer is None:
        units = [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]
        effective_max = max_tokens
    else:
        if not getattr(tokenizer, "is_fast", False):
            raise ValueError("Exact BGE chunking requires a fast tokenizer with offset mappings")
        encoding = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True, truncation=False)
        units = [tuple(map(int, offsets)) for offsets in encoding["offset_mapping"]
                 if offsets[1] > offsets[0]]
        effective_max = max_tokens - 2
    if not units:
        return []
    segments: list[Segment] = []
    at = 0
    while at < len(units):
        end_idx = min(at + effective_max, len(units))
        if end_idx < len(units) and end_idx - at >= 32:
            lower_bound = at + int(0.75*(end_idx-at))
            cuts = [i for i in range(lower_bound+1, end_idx) if
                    "\n\n" in text[units[i-1][1]:units[i][0]]]
            if cuts:
                end_idx = cuts[-1]
        start_char = units[at][0]
        end_char = units[end_idx-1][1]
        segments.append(Segment(segment_id=f"s{len(segments):04d}",
                                start=start_char, end=end_char,
                                text=text[start_char:end_char], parent_key=parent_key))
        if end_idx == len(units):
            break
        at = max(at+1, end_idx-overlap)
    return segments
