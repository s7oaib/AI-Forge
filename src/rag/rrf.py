"""Reciprocal Rank Fusion of lexical BM25 and dense vector candidate lists."""

from __future__ import annotations

from typing import Sequence

RRF_K = 60


def rrf_fuse(
    ranked_lists: Sequence[Sequence[str]],
    k: int = RRF_K,
) -> dict[str, float]:
    """Fuse multiple ranked lists of IDs into a single score map.

    rrf_score(id) = sum over lists of 1 / (k + rank), rank starting at 1.
    Higher score -> more authoritative across retrieval channels.
    """
    fused: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, item_id in enumerate(ranked, start=1):
            fused[item_id] = fused.get(item_id, 0.0) + 1.0 / (k + rank)
    return fused


def rank(fused: dict[str, float]) -> list[tuple[str, float]]:
    """Return IDs sorted by descending fused score."""
    return sorted(fused.items(), key=lambda kv: -kv[1])


def normalize(fused: dict[str, float]) -> float:
    """Best candidate's RRF demand, normalized by its theoretical max across 2 lists.

    Used by the abstention gate as a bounded [0,1] confidence signal.
    """
    if not fused:
        return 0.0
    best = max(fused.values())
    max_possible = 2.0 / (RRF_K + 1)
    return min(best / max_possible, 1.0)
