"""Provenance classification of graph edges (Constitution P5: epistemic tagging).

EXTRACTED  — explicitly present in approved document frontmatter/body text.
STRUCTURAL — programmatically derived containment/hierarchy edges.
INFERRED   — LLM-community-linker suggestions; never citable as primary facts.
"""

from enum import Enum


class Provenance(str, Enum):
    EXTRACTED = "EXTRACTED"
    STRUCTURAL = "STRUCTURAL"
    INFERRED = "INFERRED"


def classify_edge(relation: str, source_doc: str | None = None) -> Provenance:
    """Classify an edge by its relation name and optional source document."""
    from src.graph.graphify_config import STRUCTURAL_EDGES

    if relation in STRUCTURAL_EDGES:
        return Provenance.STRUCTURAL
    if source_doc is not None:
        return Provenance.EXTRACTED
    return Provenance.INFERRED
