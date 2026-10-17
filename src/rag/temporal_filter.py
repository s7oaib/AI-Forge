"""Temporal expiry guard for retrieved evidence (SEC-03 / Constitution P6)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass
class TemporalResult:
    fresh: list
    expired: list
    warnings: list[str]


def filter_chunks(chunks: Iterable, reference_date: date | None = None) -> TemporalResult:
    """Partition chunks into current vs expired by review_before_date."""
    ref = reference_date or date.today()
    fresh, expired, warnings = [], [], []
    for chunk in chunks:
        rbd = chunk.review_before_date
        if rbd and date.fromisoformat(rbd) < ref:
            expired.append(chunk)
            warnings.append(f"Excluded expired chunk {chunk.chunk_id} (reviewed-before {rbd})")
        else:
            fresh.append(chunk)
    return TemporalResult(fresh=fresh, expired=expired, warnings=warnings)


def effective_year_matches(chunk, query_year: str | None) -> bool:
    """Optionally pin all answers to one academic year (query like '2025 cutoffs')."""
    if not query_year:
        return True
    return chunk.effective_academic_year == query_year
