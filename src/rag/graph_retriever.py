"""Subgraph Evidence Extractor: connected relational triples for linked entities (T024)."""

from __future__ import annotations

from typing import Iterable, Optional


class GraphRetriever:
    def __init__(self, adapter, hop: int = 2):
        self.adapter = adapter
        self.hop = hop

    def extract(self, node_ids: Iterable[str], hop: Optional[int] = None) -> dict:
        """Merge k-hop neighborhoods of linked entities into one subgraph.

        Only citable (non-INFERRED) edges participate (Constitution P4:
        inferred edges cannot support primary facts).
        """
        hop = hop or self.hop
        merged_nodes, merged_edges, seen_edges = {}, {}, set()
        for node_id in node_ids:
            hood = self.adapter.k_hop_neighborhood(node_id, k=hop)
            for n in hood["nodes"]:
                nid = n["id"]
                if nid not in merged_nodes or merged_nodes[nid].get("aliases") in ([], None):
                    merged_nodes[nid] = n
            for e in hood["edges"]:
                if e["provenance"] == "INFERRED":
                    continue
                key = (e["source"], e["relation"], e["target"])
                if key in seen_edges:
                    continue
                seen_edges.add(key)
                merged_edges[key] = e
        return {
            "nodes": sorted(merged_nodes.values(), key=lambda n: n["id"]),
            "edges": sorted(merged_edges.values(), key=lambda e: (e["source"], e["relation"], e["target"])),
        }

    def fact_lines(self, subgraph: dict) -> list[str]:
        """Human-readable triple lines for prompt context."""
        node_names = {n["id"]: n.get("name", n["id"]) for n in subgraph["nodes"]}
        lines = []
        for e in subgraph["edges"]:
            lines.append(
                f"{node_names.get(e['source'], e['source'])} --{e['relation']}--> "
                f"{node_names.get(e['target'], e['target'])}"
            )
        return lines
