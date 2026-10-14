"""Fail-closed, bounded structured Responses API parsing.

Reasoning models can use the output budget for reasoning before emitting any JSON.
Do not interpret an empty/incomplete output as a semantic rejection of evidence.
The at-most-one retry is intentionally bounded and requires a larger output budget.
"""
from __future__ import annotations

import json
from typing import Any


class StructuredModelResponseError(ValueError):
    """The model did not provide a complete schema-conforming JSON object."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def request_json_object(*, client: Any, model: str, name: str, schema: dict[str, Any],
                        instructions: str, payload: Any, effort: str = 'medium',
                        initial_output_tokens: int = 900, attempts: int = 2,
                        verbosity: str | None = None) -> dict[str, Any]:
    if not 1 <= attempts <= 2:
        raise ValueError('attempts must be 1 or 2')
    if initial_output_tokens <= 0:
        raise ValueError('initial_output_tokens must be positive')
    content = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    last_error: StructuredModelResponseError | None = None
    for attempt in range(attempts):
        # Keep bounded; the larger retry is to handle truncated reasoning output.
        requested_output_tokens = min(4096, initial_output_tokens * (2 ** attempt))
        fmt = {'format': {'type': 'json_schema', 'name': name, 'strict': True, 'schema': schema}}
        if verbosity:
            fmt['verbosity'] = verbosity
        response = client.responses.create(
            model=model, reasoning={'effort': effort}, text=fmt,
            max_output_tokens=requested_output_tokens,
            instructions=instructions, input=content,
        )
        status = getattr(response, 'status', None)
        if status in {'incomplete', 'failed', 'cancelled'}:
            last_error = StructuredModelResponseError('response_' + status)
            continue
        output_text = getattr(response, 'output_text', None)
        if not isinstance(output_text, str) or not output_text.strip():
            last_error = StructuredModelResponseError('missing_output_text')
            continue
        try:
            data = json.loads(output_text)
        except (ValueError, TypeError):
            last_error = StructuredModelResponseError('invalid_json')
            continue
        if not isinstance(data, dict):
            last_error = StructuredModelResponseError('not_json_object')
            continue
        return data
    raise last_error or StructuredModelResponseError('unknown_model_output_failure')
