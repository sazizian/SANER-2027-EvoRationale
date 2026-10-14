"""Hard upper bounds selected before a run (paper Section V-E)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


class BudgetExhausted(RuntimeError):
    pass


@dataclass(frozen=True)
class Budget:
    max_rounds: int = 3
    max_queries: int = 12
    max_artifact_reads: int = 24
    max_input_tokens: int = 64_000
    max_output_tokens: int = 4096
    bm25_candidates: int = 50
    dense_candidates: int = 50
    rrf_k: int = 60

    def __post_init__(self) -> None:
        if min(vars(self).values()) < 1:
            raise ValueError("All budget values must be positive")

    @staticmethod
    def estimate_tokens(value: Any) -> int:
        # Offline conservative budget estimator, not exact tokenizer accounting.
        import json
        text = json.dumps(value, ensure_ascii=False)
        return max(1, (len(text.encode("utf-8")) + 2) // 3)

    def charge_tokens(self, memory: Any, payload: Any) -> None:
        count = self.estimate_tokens(payload)
        if memory.token_count + count > self.max_input_tokens:
            raise BudgetExhausted("cumulative_input_token_limit")
        memory.token_count += count

    def charge_query(self, memory: Any) -> None:
        if memory.query_count >= self.max_queries:
            raise BudgetExhausted("repository_query_limit")
        memory.query_count += 1

    def charge_reads(self, memory: Any, artifact_keys: list[str]) -> None:
        pending = [key for key in dict.fromkeys(artifact_keys) if key not in memory.artifact_reads]
        if len(memory.artifact_reads) + len(pending) > self.max_artifact_reads:
            raise BudgetExhausted("unique_artifact_read_limit")
        memory.artifact_reads.extend(pending)
