"""Honest experimental harness contracts, never synthetic replacements for paper baselines.

Original baseline forks and proprietary observations were not supplied. This module
makes those dependencies explicit instead of fabricating a 'reproduction'.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
from .budget import Budget
from .agent import EvoRationaleAgent
from .model import eligible, validate_state, normalize_history
from .retrieval import LocalHybridRetriever

BASELINES = (
    "decision_only_llm", "long_context_llm", "hybrid_rag", "kantara_reimplemented",
    "linkanchor_adapted", "experepair_adapted", "stateless_tool_agent",
)
ABLATIONS = ("without_decision_memory", "without_iterative_retrieval", "without_runtime_verification",
             "without_temporal_filter", "without_explicit_linking", "without_alloy")


class UnavailableStudyImplementation(RuntimeError):
    pass


class ExperimentalRegistry:
    def __init__(self) -> None:
        self.registered: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, implementation: Callable[..., Any]) -> None:
        if name not in BASELINES and name not in ABLATIONS:
            raise ValueError(f"Unknown prespecified experiment: {name}")
        self.registered[name] = implementation

    def run(self, name: str, *, state: dict[str, Any], history: list[dict[str, Any]],
            budget: Budget, **kwargs: Any) -> Any:
        if name not in BASELINES and name not in ABLATIONS:
            raise ValueError("Not a prespecified experiment")
        if name not in self.registered:
            raise UnavailableStudyImplementation(
                f"{name} has no validated, pinned study adapter. "
                "Provide the authentic implementation and freeze model/configuration "
                "before using this result in the paper.")
        return self.registered[name](state=validate_state(state), history=normalize_history(history),
                                     budget=budget, **kwargs)


def full_system(state: dict[str, Any], history: list[dict[str, Any]],
                budget: Budget | None = None) -> dict[str, Any]:
    return EvoRationaleAgent(budget=budget or Budget()).run(state, history).report
