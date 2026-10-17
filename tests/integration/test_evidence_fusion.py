"""M5 integration tests: multi-hop evidence fusion (T027)."""

from datetime import date
from pathlib import Path

import pytest

from src.graph.adapter import GraphAdapter
from src.index.chunker import chunk_directory, chunk_markdown_file
from src.rag.context_builder import ContextBuilder
from src.rag.entity_linker import EntityLinker
from src.rag.graph_retriever import GraphRetriever
from src.rag.temporal_filter import filter_chunks


@pytest.fixture(scope="module")
def graph():
    return GraphAdapter.load("artifacts/graph/graph.json")


def test_multi_hop_classic_query(graph):
    """'Who teaches NLP and what lab do they head?' -> 2-hop fused answer."""
    linker = EntityLinker(graph)
    linked = linker.link("Who teaches Natural Language Processing and what lab do they head?")
    ids = {l["node_id"] for l in linked}
    assert "CRS-CS402" in ids

    retriever = GraphRetriever(graph, hop=2)
    sub = retriever.extract(ids)
    facts = retriever.fact_lines(sub)
    assert any("TAUGHT_BY" in f and "Arvind Raman" in f for f in facts)
    assert any("HEAD_OF" in f and "Language Technologies Research Center" in f for f in facts)


def test_staging_corpus_never_enters_pipeline(graph, tmp_path):
    """A document in knowledge/staging/ must never be retrievable (SEC-01)."""
    bad = tmp_path / "leaked.md"
    bad.write_text("no frontmatter here — tofu scraping", "utf-8")
    chunks = chunk_directory(tmp_path)  # staging dir content, unparseable
    assert chunks == []


def test_temporal_filter_marks_expired_chunks(tmp_path):
    stale = tmp_path / "stale_record.md"
    stale.write_text(
        """---
id: DOC-STALE-TEST
title: "Old Fee Circular (stale test fixture)"
category: fees_scholarships
slug: stale-circular
official_url: "https://greenfield.edu/fees/old"
source_retrieval_date: 2024-01-01
approval_status: approved
approved_by: "provost-desk@greenfield.edu"
approval_date: 2024-01-01
last_verified_date: 2024-01-01
effective_academic_year: "2024-2025"
review_before_date: 2025-01-01
---

# Old Fee Circular (post-expiry fixture)
- Fee: 99,000 rupees (no longer effective)
""",
        "utf-8",
    )
    chunks = chunk_markdown_file(stale)
    res = filter_chunks(chunks, reference_date=date(2026, 10, 17))
    assert not res.fresh
    assert len(res.expired) == len(chunks)
    assert res.warnings and all("expired" in w for w in res.warnings)


def test_fresh_chunks_survive_temporal_filter(graph):
    chunks = chunk_directory(Path("knowledge/approved"))
    res = filter_chunks(chunks, reference_date=date(2026, 10, 17))
    assert not res.expired
    assert len(res.fresh) == len(chunks)


def test_context_builder_assembles_isolated_evidence(graph):
    chunks = chunk_directory(Path("knowledge/approved"))
    target = [c for c in chunks if c.doc_id == "DOC-CRS-CS402"]
    retriever = GraphRetriever(graph, hop=2)
    sub = retriever.extract({"CRS-CS402"})
    ctx = ContextBuilder().build(target, sub, retriever.fact_lines(sub))
    assert ctx["xml"].startswith("<evidence>")
    assert "DOC-CRS-CS402::" in ctx["xml"]
    assert "graph_facts" in ctx["xml"]
    assert "CrS" not in ctx["xml"]  # tags are lowercase/canonical: sanity
    assert all(cid.startswith("DOC-CRS-CS402") for cid in ctx["chunk_ids"])


def test_linker_prefers_longest_alias(graph):
    linker = EntityLinker(graph)
    linked = linker.link("natural language processing")
    first = linked[0]
    # Longest alias wins before the short 'nlp' alias can shadow it.
    assert first["matched_alias"] == "natural language processing"
    assert first["node_id"] == "CRS-CS402"


def test_linker_geographic_question(graph):
    linker = EntityLinker(graph)
    linked = linker.link("Where is the Language Technologies Research Center located?")
    ids = {l["node_id"] for l in linked}
    assert "FAC-LTRC" in ids
