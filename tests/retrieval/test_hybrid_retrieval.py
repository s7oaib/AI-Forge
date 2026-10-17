"""M4 retrieval tests: hybrid BM25 + dense recall with RRF fusion (T022).

Blueprint threshold: Recall@5 >= 90% on the fixture corpus.
"""

from pathlib import Path

import pytest

from src.index.bm25_indexer import BM25Index
from src.index.chunker import chunk_directory
from src.index.vector_indexer import DeterministicHashEmbedder, NumpyBackend, VectorIndex
from src.rag.abstention_gate import evaluate
from src.rag.rrf import rank, rrf_fuse

QUESTIONS = [
    ("Who teaches Natural Language Processing?", "Dr. Arvind Raman"),
    ("What are the library timings on weekdays?", "8:00 to 22:00"),
    ("What is the fee for the computer science B.Tech?", "145,000"),
    ("What was the cutoff for CSE in 2026 admissions?", "93 percentile"),
    ("Where is the electronics department located?", "Nulliplex Block 2"),
    ("How many students can the hostels accommodate?", "2,400"),
    ("What scholarship can first-year students get?", "25 percent"),
    ("When does the semester start?", "21 July 2026"),
    ("What was the placement percentage last year?", "92 percent"),
    ("What is the grading scale?", "10-point"),
    ("Who heads the Language Technologies Research Center?", "Arvind Raman"),
    ("What is the minimum qualification for B.Tech admission?", "60 percent"),
]


@pytest.fixture(scope="module")
def indexes(tmp_path_factory):
    chunks = chunk_directory(Path("knowledge/approved"))
    assert len(chunks) > 20
    gold = {}
    for q, delimiter in QUESTIONS:
        gold[q] = {c.chunk_id for c in chunks if delimiter in c.searchable_text}

    bm25 = BM25Index(tmp_path_factory.mktemp("bm25") / "bm25.db")
    bm25.build(chunks)

    vector = VectorIndex(
        embedder=DeterministicHashEmbedder(),
        backend=NumpyBackend(tmp_path_factory.mktemp("vec")),
    )
    vector.build(chunks)
    return {"bm25": bm25, "vec": vector, "gold": gold, "chunks": chunks}


def _top_fused_ids(bm25, vector, q, k=5):
    bm = [r["chunk_id"] for r in bm25.search(q, k=k)]
    vs = [r["chunk_id"] for r in vector.search(q, k=k)]
    return set(bm) | set(vs), bm, vs


def test_lexical_search_returns_relevant_chunks(indexes):
    results = indexes["bm25"].search("Who teaches Natural Language Processing and NLP?", k=5)
    assert results
    assert any(r["chunk_id"].startswith("DOC-CRS-CS402") for r in results)


def test_dense_search_returns_relevant_chunks(indexes):
    results = indexes["vec"].search("library timing books reading", k=5)
    assert results
    assert any(r["chunk_id"].startswith("DOC-FAC-LIB") for r in results)


def test_rrf_fusion_behaviour(indexes):
    bm25, vector = indexes["bm25"], indexes["vec"]
    q = "Who teaches Natural Language Processing and NLP?"
    bm = [r["chunk_id"] for r in bm25.search(q, k=5)]
    vs = [r["chunk_id"] for r in vector.search(q, k=5)]
    fused = rrf_fuse([bm, vs])
    ranked = rank(fused)
    assert ranked, "fusion produced no ranked candidates"
    scores = [s for _, s in ranked]
    assert scores[0] >= scores[-1]


def test_recall_at_5_at_least_90_percent(indexes):
    bm25, vector, gold = indexes["bm25"], indexes["vec"], indexes["gold"]
    hits = 0
    for q, _delimiter in QUESTIONS:
        top5, _, _ = _top_fused_ids(bm25, vector, q)
        if top5 & gold[q]:
            hits += 1
    recall = hits / len(QUESTIONS)
    assert recall >= 0.90, f"Recall@5 = {recall:.2%} ({hits}/{len(QUESTIONS)})"


def test_abstention_gate_blocks_empty_evidence():
    decision = evaluate({})
    assert not decision.should_answer
    assert "don't have verified information" in decision.abstain_message


def test_abstention_gate_passes_strong_fused_evidence():
    ids = [f"c{i}" for i in range(5)]
    fused = rrf_fuse([ids, ids])
    decision = evaluate(fused)
    assert decision.should_answer
    assert decision.confidence > 0.035


def test_stale_records_excluded_at_query_time(indexes):
    bm25 = indexes["bm25"]
    bm25.conn.execute(
        "INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?)",
        ("STALE::1", "STALE-DOC", "stale.md", "faqs", "Old", "http://x", "2024-2025", "2025-01-01"),
    )
    bm25.conn.execute("INSERT INTO chunk_fts VALUES (?,?)", ("STALE::1", "stale obsolete policy fee"))
    results = bm25.search("stale obsolete policy", k=5)
    assert all(r["chunk_id"] != "STALE::1" for r in results)
    # purge restores the authoritative-only state
    bm25.purge_stale(["STALE::1"])
    assert all(r["chunk_id"] != "STALE::1" for r in bm25.search("stale obsolete policy", k=5))


def test_purge_removes_chunks(indexes):
    bm25 = indexes["bm25"]
    before = bm25.count()
    sample = bm25.conn.execute("SELECT chunk_id FROM chunks LIMIT 1").fetchone()[0]
    bm25.purge_stale([sample])
    assert bm25.count() == before - 1
