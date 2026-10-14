"""Fail-closed, bounded structured Responses API JSON-object parsing.

Reasoning models can use the output budget for reasoning before emitting any JSON.
Do not interpret an empty/incomplete output as a semantic rejection of evidence.
The at-most-one retry is intentionally bounded and requires a larger output budget.
"""
from __future__ import annotations

import json
import math
from typing import Any


class StructuredModelResponseError(ValueError):
    """The model did not provide a complete, unambiguous JSON object.

    Callers separately validate their complete domain-specific response schema.
    """

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            # Last-value-wins can turn a negative semantic vote into a positive
            # one, or silently replace a batch's decisions. Never choose a side.
            raise StructuredModelResponseError('duplicate_json_key')
        result[key] = value
    return result


def _nonfinite_constant(_: str) -> Any:
    raise StructuredModelResponseError('nonfinite_json_number')


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise StructuredModelResponseError('nonfinite_json_number')
    return parsed


def request_json_object(*, client: Any, model: str, name: str, schema: dict[str, Any],
                        instructions: str, payload: Any, effort: str = 'medium',
                        initial_output_tokens: int = 900, attempts: int = 2,
                        verbosity: str | None = None,
                        output_token_ceiling: int = 4096,
                        before_request: Any = None,
                        after_response: Any = None) -> dict[str, Any]:
    if type(attempts) is not int or not 1 <= attempts <= 2:
        raise ValueError('attempts must be 1 or 2')
    if type(initial_output_tokens) is not int or initial_output_tokens <= 0:
        raise ValueError('initial_output_tokens must be a positive integer')
    if type(output_token_ceiling) is not int or output_token_ceiling <= 0:
        raise ValueError('output_token_ceiling must be a positive integer')
    content = (payload if isinstance(payload, str)
               else json.dumps(payload, ensure_ascii=False, allow_nan=False))
    last_error: StructuredModelResponseError | None = None
    for attempt in range(attempts):
        # Keep bounded; the larger retry is to handle truncated reasoning output.
        requested_output_tokens = min(output_token_ceiling, initial_output_tokens * (2 ** attempt))
        fmt = {'format': {'type': 'json_schema', 'name': name, 'strict': True, 'schema': schema}}
        if verbosity:
            fmt['verbosity'] = verbosity
        request = dict(model=model, reasoning={'effort': effort}, text=fmt,
                       max_output_tokens=requested_output_tokens,
                       instructions=instructions, input=content)
        # The event-complete profile reserves the actual request envelope,
        # including schemas/instructions, before EACH call or bounded retry.
        # The legacy callers deliberately retain their existing accounting.
        if before_request is not None:
            before_request(request)
        response = client.responses.create(**request)
        if after_response is not None:
            after_response(response)
        status = getattr(response, 'status', None)
        # A nonterminal response's text is not a final semantic verdict. Missing
        # status is retained solely for the existing lightweight test adapters.
        if status is not None and status != 'completed':
            code = 'response_' + status if isinstance(status, str) else 'invalid_response_status'
            last_error = StructuredModelResponseError(code)
            continue
        output_text = getattr(response, 'output_text', None)
        if not isinstance(output_text, str) or not output_text.strip():
            last_error = StructuredModelResponseError('missing_output_text')
            continue
        try:
            data = json.loads(output_text, object_pairs_hook=_unique_object,
                              parse_constant=_nonfinite_constant, parse_float=_finite_float)
        except StructuredModelResponseError as exc:
            last_error = exc
            continue
        except (ValueError, TypeError):
            last_error = StructuredModelResponseError('invalid_json')
            continue
        if not isinstance(data, dict):
            last_error = StructuredModelResponseError('not_json_object')
            continue
        return data
    raise last_error or StructuredModelResponseError('unknown_model_output_failure')
