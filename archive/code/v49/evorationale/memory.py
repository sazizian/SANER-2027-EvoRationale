"""Decision-centered memory: verified links, unresolved needs, rejected interpretations, feedback.

The working state is isolated per run and never updates authoritative S0. MongoDB
adapter stores immutable checkpoints; in-memory and JSON alternatives are available offline.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, asdict
import json
from pathlib import Path
from typing import Any, Protocol


@dataclass
class DecisionMemory:
    run_id: str
    initial_state: dict[str, Any]
    needs: list[dict[str, Any]] = field(default_factory=list)
    verified_links: list[dict[str, Any]] = field(default_factory=list)
    rejected_interpretations: list[dict[str, Any]] = field(default_factory=list)
    technical_verification_failures: list[dict[str, Any]] = field(default_factory=list)
    verifier_feedback: list[dict[str, Any]] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    attempts: list[str] = field(default_factory=list)
    query_count: int = 0
    artifact_reads: list[str] = field(default_factory=list)
    round_count: int = 0
    token_count: int = 0
    report: dict[str, Any] | None = None
    status: str = "CREATED"
    human_reviews: list[dict[str, Any]] = field(default_factory=list)
    # Run-local exact-proposal verifier decisions. Each cache key includes the
    # artifact-version identity, claim, relation, and proposed provenance.
    # A changed quote/version is reverified instead of reusing a verdict.
    reviewed_proposals: dict[str, dict[str, Any]] = field(default_factory=dict)

    def record_link(self, link: dict[str, Any]) -> None:
        key = (link["artifact_key"], link["decision_element_id"], link["relation"])
        if key not in {(x["artifact_key"], x["decision_element_id"], x["relation"]) for x in self.verified_links}:
            self.verified_links.append(deepcopy(link))

    def asdict(self) -> dict[str, Any]:
        return asdict(self)


class MemoryStore(Protocol):
    def save(self, record: DecisionMemory) -> None: ...
    def get(self, run_id: str) -> DecisionMemory | None: ...


class MemoryInProcess:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}
        self.checkpoint_counts: dict[str, int] = {}

    def save(self, record: DecisionMemory) -> None:
        self.records[record.run_id] = deepcopy(record.asdict())
        self.checkpoint_counts[record.run_id] = self.checkpoint_counts.get(record.run_id, 0) + 1

    def get(self, run_id: str) -> DecisionMemory | None:
        return DecisionMemory(**deepcopy(self.records[run_id])) if run_id in self.records else None


class FileMemory:
    def __init__(self, directory: str | Path) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, record: DecisionMemory) -> None:
        path = self.dir / f"{record.run_id}.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(record.asdict(), indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)

    def get(self, run_id: str) -> DecisionMemory | None:
        path = self.dir / f"{run_id}.json"
        return DecisionMemory(**json.loads(path.read_text(encoding="utf-8"))) if path.exists() else None


class MongoMemory:
    def __init__(self, uri: str, database: str) -> None:
        try:
            from pymongo import MongoClient
        except ImportError as exc:
            raise RuntimeError("Install pymongo to use MongoDB memory") from exc
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.client.admin.command("ping")
        self.collection = self.client[database]["decision_runs"]
        self.collection.create_index("run_id", unique=True)

    def save(self, record: DecisionMemory) -> None:
        self.collection.replace_one({"_id": record.run_id}, {"_id": record.run_id, **record.asdict()}, upsert=True)

    def get(self, run_id: str) -> DecisionMemory | None:
        data = self.collection.find_one({"_id": run_id})
        if data is None:
            return None
        data.pop("_id")
        return DecisionMemory(**data)
