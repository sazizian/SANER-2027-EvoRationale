"""Repository-disjoint held-out metric aggregation and statistical utilities.

These utilities do NOT generate missing empirical observations. They operate only
on actual supplied predictions, references and logged repetitions.
"""
from __future__ import annotations
from collections import defaultdict
import random
from statistics import mean
from typing import Any

from .model import DRIFT_TYPES, OUTCOMES

DRIFT_LABELS = tuple(sorted(set(DRIFT_TYPES.values())))
OUTCOME_LABELS = ("KEEP", "REVALIDATE", "REVISE", "REOPEN")


def set_precision_recall_f1(pred: set[Any], gold: set[Any]) -> dict[str, float]:
    tp = len(pred & gold)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(gold) if gold else 0.0
    return {"precision": p, "recall": r, "f1": 2*p*r/(p+r) if p+r else 0.0}


def multiclass_macro_f1(pred: list[str], gold: list[str], labels: tuple[str, ...]) -> float:
    if len(pred) != len(gold) or not pred:
        raise ValueError("Nonempty, equal-length predictions and references required")
    values = []
    for label in labels:
        tp = sum(a == label and b == label for a, b in zip(pred, gold))
        fp = sum(a == label and b != label for a, b in zip(pred, gold))
        fn = sum(a != label and b == label for a, b in zip(pred, gold))
        values.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0)
    return mean(values)


def multilabel_macro_f1(pred: list[set[str]], gold: list[set[str]],
                         labels: tuple[str, ...] = DRIFT_LABELS) -> float:
    if len(pred) != len(gold) or not pred:
        raise ValueError("Nonempty, equal-length predictions and references required")
    return mean(multiclass_macro_f1(["P" if label in p else "N" for p in pred],
                                    ["P" if label in g else "N" for g in gold], ("P",))
                for label in labels)


def reference_sets(report: dict[str, Any], gold: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Artifact/version-level scoring when gold has a version; legacy demo uses artifact ID."""
    def id_of(x: dict[str, Any]) -> str:
        if x.get("artifact_key"):
            return x["artifact_key"]
        if x.get("artifact_id"):
            return x["artifact_id"]
        raise ValueError("Evidence record must have artifact_key or artifact_id")
    pred_links = report["verified_evidence"]
    ref_links = gold.get("evidence_links", [])
    prediction = {
        "evidence": {id_of(x) for x in pred_links},
        "links": {(id_of(x), x["decision_element_id"]) for x in pred_links},
        "relations": {(id_of(x), x["decision_element_id"], x["relation"]) for x in pred_links},
    }
    reference = {
        "evidence": {id_of(x) for x in ref_links},
        "links": {(id_of(x), x["decision_element_id"]) for x in ref_links},
        "relations": {(id_of(x), x["decision_element_id"], x["relation"]) for x in ref_links},
    }
    return {metric: set_precision_recall_f1(prediction[metric], reference[metric]) for metric in prediction}


def repository_weighted_scores(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Compute per-repetition, per-repository metrics; average runs within repositories then repositories.

    Each row: repository, repetition, predicted_outcome, gold_outcome,
    predicted_drift (list), gold_drift (list), evidence_f1, link_f1, relation_f1, ucr.
    """
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["repository"], int(row["repetition"])].append(row)
    per_repo: dict[str, list[dict[str, float]]] = defaultdict(list)
    for (repo, _), observations in grouped.items():
        per_repo[repo].append({
            "outcome_macro_f1": multiclass_macro_f1(
                [x["predicted_outcome"] for x in observations],
                [x["gold_outcome"] for x in observations], OUTCOME_LABELS),
            "drift_macro_f1": multilabel_macro_f1(
                [set(x["predicted_drift"]) for x in observations],
                [set(x["gold_drift"]) for x in observations]),
            **{name: mean(x[name] for x in observations) for name in
               ("evidence_f1", "link_f1", "relation_f1", "ucr")},
        })
    fields = ("outcome_macro_f1", "drift_macro_f1", "evidence_f1", "link_f1", "relation_f1", "ucr")
    return {name: mean(mean(run[name] for run in repo_runs) for repo_runs in per_repo.values())
            for name in fields}


def paired_repository_bootstrap(left: dict[str, float], right: dict[str, float],
                                iterations: int = 10_000, seed: int = 2027) -> dict[str, Any]:
    if set(left) != set(right) or not left:
        raise ValueError("Both methods must contain exactly the same repositories")
    rng = random.Random(seed)
    repositories = sorted(left)
    paired = [left[k] - right[k] for k in repositories]
    draws = sorted(mean(rng.choices(paired, k=len(paired))) for _ in range(iterations))
    return {"paired_difference": mean(paired),
            "ci_95": [draws[int(0.025*(iterations-1))], draws[int(0.975*(iterations-1))]],
            "n_repositories": len(repositories)}


def holm_adjust(pvalues: list[float]) -> list[float]:
    if any(not 0 <= x <= 1 for x in pvalues):
        raise ValueError("p-values must be between zero and one")
    m = len(pvalues)
    ordering = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0]*m
    running = 0.0
    for rank, i in enumerate(ordering):
        running = max(running, min(1.0, (m-rank)*pvalues[i]))
        adjusted[i] = running
    return adjusted


def paired_wilcoxon(left: dict[str, float], right: dict[str, float]) -> dict[str, Any]:
    if set(left) != set(right) or not left:
        raise ValueError("Matched nonempty repository set required")
    try:
        from scipy.stats import wilcoxon, rankdata
    except ImportError as exc:
        raise RuntimeError("Install optional research dependencies for Wilcoxon analysis") from exc
    differences = [left[k]-right[k] for k in sorted(left)]
    if all(value == 0 for value in differences):
        return {"pvalue": 1.0, "r_rank_biserial": 0.0}
    _, p = wilcoxon(differences, zero_method="pratt", alternative="two-sided", method="auto")
    # Pratt zero convention: zero differences participate in the ranking of
    # |differences|, but contribute to neither signed-rank sum.
    ranks = rankdata([abs(value) for value in differences], method="average")
    positive = sum(rank for rank, delta in zip(ranks, differences) if delta > 0)
    negative = sum(rank for rank, delta in zip(ranks, differences) if delta < 0)
    return {"pvalue": float(p), "r_rank_biserial": (positive-negative)/(positive+negative)}
