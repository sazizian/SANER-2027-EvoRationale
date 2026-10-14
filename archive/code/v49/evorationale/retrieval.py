"""Temporal, repository-scoped BM25 + optional dense BGE-M3 retrieval using RRF(k=60).

Unlike the original package, ES stores every artifact VERSION with a distinct key,
never overwriting edited issues/PRs. Mandatory eligibility is checked on BOTH sides.
"""
from __future__ import annotations

from collections import Counter
import math
import re
from typing import Any, Protocol

from .model import artifact_key, eligible
from .segmentation import segment_text


def artifact_text(a: dict[str, Any]) -> str:
    return f"{a['title']}\n{a['content']}\n{' '.join(a.get('tags', []))}"


def reciprocal_rank_fusion(ranked_lists: list[list[str]], limit: int, k: int = 60) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranking in ranked_lists:
        for rank, key in enumerate(dict.fromkeys(ranking), 1):
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))[:limit]


class Retriever(Protocol):
    def index(self, artifacts: list[dict[str, Any]]) -> None: ...
    def search(self, state: dict[str, Any], question: dict[str, Any], limit: int,
               sparse_candidates: int = 50, dense_candidates: int = 50, rrf_k: int = 60) -> list[dict[str, Any]]: ...


class LocalHybridRetriever:
    def __init__(self, embedder: Any = None) -> None:
        self.documents: dict[str, dict[str, Any]] = {}
        self.embedder = embedder
        self.vectors: dict[str, list[float]] = {}
        self.segments: dict[str, dict[str, Any]] = {}

    def index(self, artifacts: list[dict[str, Any]]) -> None:
        self.documents = {artifact_key(a): a for a in artifacts}
        self.segments = {}
        for parent_key, a in self.documents.items():
            for segment in segment_text(artifact_text(a), parent_key, tokenizer=getattr(self.embedder, "tokenizer", None)):
                self.segments[f"{parent_key}::{segment.segment_id}"] = {
                    "text": segment.text, "parent_key": parent_key,
                    "segment_id": segment.segment_id, "start": segment.start, "end": segment.end}
        self.vectors = {}
        if self.embedder and self.segments:
            vectors = self.embedder.encode([s["text"] for s in self.segments.values()])
            self.vectors = dict(zip(self.segments, vectors))

    def search(self, state: dict[str, Any], question: dict[str, Any], limit: int,
               sparse_candidates: int = 50, dense_candidates: int = 50, rrf_k: int = 60) -> list[dict[str, Any]]:
        eligible_segments = {key: segment for key, segment in self.segments.items()
                             if eligible(state, self.documents[segment["parent_key"]])}
        if not eligible_segments or limit <= 0:
            return []
        query = question["query"]
        # Genuine length-normalized Okapi BM25, not set-intersection IDF.
        # All document counts and lengths are computed from the *eligible* snapshot.
        def words(value: str) -> list[str]:
            return [w for w in re.findall(r"[a-z0-9][a-z0-9_+-]+", value.lower()) if len(w) >= 3]
        terms = set(words(query))
        frequencies = {key: Counter(words(segment["text"]))
                       for key, segment in eligible_segments.items()}
        df = Counter(term for freqs in frequencies.values() for term in freqs)
        n = len(eligible_segments)
        lengths = {key: sum(freq.values()) for key, freq in frequencies.items()}
        average_length = max(1.0, sum(lengths.values()) / n)
        k1, b = 1.2, 0.75
        def bm25(key: str) -> float:
            norm = k1 * (1-b + b * lengths[key] / average_length)
            return sum(math.log1p((n-df[term]+0.5)/(df[term]+0.5)) *
                       (frequencies[key][term] * (k1+1)) / (frequencies[key][term] + norm)
                       for term in terms & frequencies[key].keys())
        sparse = sorted((key for key in eligible_segments if bm25(key) > 0),
                        key=lambda key: (-bm25(key), key))[:sparse_candidates]
        rankings = [sparse]
        if self.embedder:
            query_vector = self.embedder.encode([query])[0]
            def cosine(key: str) -> float:
                vector = self.vectors[key]
                num = sum(a*b for a,b in zip(vector,query_vector))
                denom = (sum(a*a for a in vector)*sum(b*b for b in query_vector))**0.5
                return num / denom if denom else -1
            dense = sorted(eligible_segments, key=lambda key: (-cosine(key),key))[:dense_candidates]
            rankings.append(dense)
        # RRF at segment level; consolidate parent artifact/version IDs AFTER fusion.
        selected: dict[str, float] = {}
        for key, score in reciprocal_rank_fusion(rankings, len(eligible_segments), rrf_k):
            parent = eligible_segments[key]["parent_key"]
            selected[parent] = max(selected.get(parent, 0.0), score)
        ordered = sorted(selected, key=lambda key: (-selected[key], key))[:limit]
        return [{**self.documents[key], "retrieval_score": round(selected[key],8)} for key in ordered]


class BgeM3Embedder:
    def __init__(self, revision: str, device: str = "cpu") -> None:
        if not revision:
            raise ValueError("Pin a specific BGE-M3 model revision for reproducibility")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("pip install sentence-transformers for BGE-M3") from exc
        self.model = SentenceTransformer("BAAI/bge-m3", revision=revision, device=device)
        self.tokenizer = self.model.tokenizer
        if not getattr(self.tokenizer, "is_fast", False):
            raise RuntimeError("BGE-M3 requires a fast tokenizer for exact segment offsets")

    def encode(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()


class ElasticsearchHybridRetriever:
    """Optional production backend. All returned hits are rechecked against trusted history."""
    def __init__(self, url: str, index: str, embedder: Any) -> None:
        try:
            from elasticsearch import Elasticsearch
        except ImportError as exc:
            raise RuntimeError("pip install elasticsearch to use this backend") from exc
        self.client = Elasticsearch(url)
        self.index_name = index
        self.embedder = embedder
        self.canonical: dict[str, dict[str, Any]] = {}

    def index(self, artifacts: list[dict[str, Any]]) -> None:
        self.canonical = {artifact_key(a): a for a in artifacts}
        if not artifacts:
            return
        entries = []
        for a in artifacts:
            parent = artifact_key(a)
            for segment in segment_text(artifact_text(a),parent,tokenizer=getattr(self.embedder,"tokenizer",None)):
                entries.append((a,segment))
        if not entries:
            return
        vectors = self.embedder.encode([segment.text for _,segment in entries])
        dims = len(vectors[0])
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(index=self.index_name, mappings={"properties": {
                "repository": {"type": "keyword"}, "first_auditable_at": {"type": "date"},
                "text": {"type": "text"},
                "embedding": {"type": "dense_vector", "dims": dims, "index": True, "similarity": "cosine"}}})
        actions = []
        for (a, segment), vector in zip(entries, vectors):
            key = f"{artifact_key(a)}::{segment.segment_id}"
            actions += [{"index": {"_index": self.index_name, "_id": key}},
                        {"repository": a["repository"], "first_auditable_at": a["first_auditable_at"],
                         "text": segment.text, "embedding": vector}]
        self.client.bulk(operations=actions, refresh=True)

    def search(self, state: dict[str, Any], question: dict[str, Any], limit: int,
               sparse_candidates: int = 50, dense_candidates: int = 50, rrf_k: int = 60) -> list[dict[str, Any]]:
        if limit < 1:
            return []
        guards = [{"term": {"repository": state["repository"]}},
                  {"range": {"first_auditable_at": {"gt": state["accepted_at"], "lte": state["cutoff_at"]}}}]
        query = question["query"]
        sparse = self.client.search(index=self.index_name, size=sparse_candidates,
                    query={"bool": {"must": [{"match": {"text": query}}], "filter": guards}})
        query_vector = self.embedder.encode([query])[0]
        dense = self.client.search(index=self.index_name, size=dense_candidates,
                    knn={"field": "embedding", "query_vector": query_vector,
                         "k": dense_candidates, "num_candidates": max(100, 2*dense_candidates),
                         "filter": {"bool": {"filter": guards}}})
        rankings = [[hit["_id"] for hit in result["hits"]["hits"]] for result in (sparse, dense)]
        fused = reciprocal_rank_fusion(rankings, sum(map(len,rankings)), rrf_k)
        parents: dict[str,float] = {}
        for key,score in fused:
            parent = key.rsplit("::s",1)[0]
            if parent in self.canonical and eligible(state,self.canonical[parent]):
                parents[parent] = max(score,parents.get(parent,0.0))
        ordered=sorted(parents,key=lambda k:(-parents[k],k))[:limit]
        # Crucial: no external search result can bypass the independently held snapshot.
        return [{**self.canonical[k],"retrieval_score":round(parents[k],8)} for k in ordered]
