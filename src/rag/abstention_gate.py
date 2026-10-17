"""Evidence confidence filter and abstention gate (Constitution P2/P4).

If no evidence candidate clears the confidence threshold, the pipeline must
explicitly abstain rather than permit unfounded generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

DEFAULT_ABS_THRESHOLD = 0.035


@dataclass
class GateDecision:
    should_answer: bool
    confidence: float
    reasons: list[str] = field(default_factory=list)

    @property
    def abstain_message(self) -> str:
        return (
            "I don't have verified information about that in the approved college "
            "records. Please consult the official college website or the "
            "admissions office."
        )


def evaluate(
    fused_scores: dict[str, float],
    threshold: float = DEFAULT_ABS_THRESHOLD,
    normalized: Optional[float] = None,
) -> GateDecision:
    """Decide whether the evidence pool is sufficient to answer.

    normalized confidence must be computed with rrf.normalize().
    """
    if normalized is None:
        from src.rag.rrf import normalize as _norm

        normalized = _norm(fused_scores)
    reasons = []
    should = normalized >= threshold and bool(fused_scores)
    if not fused_scores or not should:
        reasons.append("No candidate exceeded the evidence confidence threshold")
    return GateDecision(should_answer=should, confidence=normalized, reasons=reasons)
