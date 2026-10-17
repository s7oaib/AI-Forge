"""M3 integration tests: graph build fidelity and traversal latency (T016)."""

import time
from pathlib import Path

import pytest

from src.admin.build_graph import build_graph
from src.graph.adapter import GraphAdapter
from src.graph.edge_classifier import Provenance


@pytest.fixture(scope="module")
def tmp_graph(tmp_path_factory):
    out = tmp_path_factory.mktemp("graph") / "graph.json"
    g = build_graph("knowledge/approved", str(out))
    return g, out


def test_graph_build_fidelity(tmp_graph):
    g, _ = tmp_graph
    by_prov = {}
    for e in g["edges"]:
        by_prov[e["provenance"]] = by_prov.get(e["provenance"], 0) + 1
    assert by_prov.get(Provenance.EXTRACTED.value, 0) > 10
    assert by_prov.get(Provenance.STRUCTURAL.value, 0) >= 3
    # Node universe covers declared entities
    ids = {n["id"] for n in g["nodes"]}
    for expected in ("COL-CORE", "DEPT-CSE", "PRG-BTECH", "CRS-CS402", "FAC-001", "FAC-LTRC"):
        assert expected in ids


def test_graph_written_and_loadable(tmp_graph):
    _, out = tmp_graph
    assert out.exists()
    adapter = GraphAdapter.load(out)
    assert adapter.stats()["nodes"] > 10
    assert adapter.stats()["edges"] > 10


def test_entity_resolution_by_name_and_alias(tmp_graph):
    _, out = tmp_graph
    adapter = GraphAdapter.load(out)
    assert adapter.find_node("Dr. Arvind Raman") == "FAC-001"
    assert adapter.find_node("natural language processing") in ("CRS-CS402",)


def test_multi_hop_query(tmp_graph):
    """'Who teaches NLP and what lab do they head?' needs a 2-hop walk:
    CRS-CS402 -TAUGHT_BY-> FAC-001 -HEAD_OF-> FAC-LTRC."""
    _, out = tmp_graph
    adapter = GraphAdapter.load(out)
    course = adapter.find_node("natural language processing")
    hood = adapter.k_hop_neighborhood(course, k=2)
    node_ids = {n["id"] for n in hood["nodes"]}
    assert "FAC-001" in node_ids
    assert "FAC-LTRC" in node_ids
    relations = {(e["source"], e["relation"], e["target"]) for e in hood["edges"]}
    assert ("CRS-CS402", "TAUGHT_BY", "FAC-001") in relations or (
        "FAC-001",
        "TEACHES",
        "CRS-CS402",
    ) in relations
    assert ("FAC-001", "HEAD_OF", "FAC-LTRC") in relations


def test_inferred_edges_not_citable(tmp_graph):
    _, out = tmp_graph
    adapter = GraphAdapter.load(out)
    # Inject an INFERRED edge to prove the citable filter excludes it.
    adapter.g.add_edge("FAC-001", "HOS-GANGA", relation="INFERRED_LINK", provenance="INFERRED", source_doc=None)
    citable = {(t["source"], t["target"]) for t in adapter.citable_triples("FAC-001")}
    assert ("FAC-001", "HOS-GANGA") not in citable
    assert any(rel == "HEAD_OF" for rel in [t["relation"] for t in adapter.citable_triples("FAC-001")])


def test_traversal_latency_under_10ms(tmp_graph):
    _, out = tmp_graph
    adapter = GraphAdapter.load(out)
    course = adapter.find_node("natural language processing")
    start = time.perf_counter()
    for _ in range(50):
        adapter.k_hop_neighborhood(course, k=2)
    elapsed_ms = (time.perf_counter() - start) / 50 * 1000
    assert elapsed_ms < 10.0, f"avg k-hop query took {elapsed_ms:.2f}ms"


def test_shortest_path(tmp_graph):
    _, out = tmp_graph
    adapter = GraphAdapter.load(out)
    path = adapter.shortest_path("COL-CORE", "FAC-001")
    assert path is not None
    assert path[0] == "COL-CORE" and path[-1] == "FAC-001"


def test_missing_node_queries_are_safe(tmp_graph):
    _, out = tmp_graph
    adapter = GraphAdapter.load(out)
    assert adapter.find_node("nonexistent thing") is None
    assert adapter.k_hop_neighborhood("NONE", k=2) == {"nodes": [], "edges": []}
    assert adapter.shortest_path("NONE", "FAC-001") is None
    assert adapter.triples("NONE") == []
