"""In-memory NetworkX graph adapter reading Graphify-compatible graph.json.

ADR-004: graph queries are answered from an in-memory structure (sub-5 ms)
rather than spawning the Graphify CLI per query.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import networkx as nx


class GraphAdapter:
    """Mutable-at-load, read-only-at-runtime directed knowledge graph."""

    def __init__(self, graph: dict):
        self.meta: dict = graph.get("meta", {})
        self.g: nx.DiGraph = nx.DiGraph()
        for node in graph.get("nodes", []):
            self.g.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})
        for edge in graph.get("edges", []):
            self.g.add_edge(
                edge["source"],
                edge["target"],
                relation=edge["relation"],
                provenance=edge.get("provenance", "EXTRACTED"),
                source_doc=edge.get("source_doc"),
            )
        self._alias_index: dict[str, str] = {}
        for node_id, attrs in self.g.nodes(data=True):
            for alias in attrs.get("aliases", []) or []:
                self._alias_index.setdefault(alias.lower().strip(), node_id)
            self._alias_index.setdefault(attrs.get("name", "").lower().strip(), node_id)

    @classmethod
    def load(cls, path: str | Path) -> "GraphAdapter":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data)

    # -- lookup ----------------------------------------------------------

    def find_node(self, name_or_alias: str) -> Optional[str]:
        """Resolve an entity node id by canonical name or alias (case-insensitive)."""
        key = name_or_alias.lower().strip()
        return self._alias_index.get(key)

    def node(self, node_id: str) -> Optional[dict]:
        if node_id in self.g:
            return {"id": node_id, **self.g.nodes[node_id]}
        return None

    # -- traversal ---------------------------------------------------------

    def k_hop_neighborhood(self, node_id: str, k: int = 1, relations: Optional[set[str]] = None) -> dict:
        """Return the k-hop ego subgraph as {nodes:[...], edges:[...]}."""
        if node_id not in self.g:
            return {"nodes": [], "edges": []}
        seen_nodes = {node_id}
        seen_edges: list[dict] = []
        frontier = {node_id}
        for _ in range(max(k, 0)):
            nxt: set[str] = set()
            for u in frontier:
                for rel_u, rel_v, d in list(self.g.out_edges(u, data=True)) + list(
                    self.g.in_edges(u, data=True)
                ):
                    other = rel_v if rel_u == u else rel_u
                    if relations is not None and d["relation"] not in relations:
                        continue
                    seen_edges.append(
                        {
                            "source": rel_u if rel_u == u else rel_v,
                            "relation": d["relation"],
                            "target": rel_v if rel_u == u else rel_u,
                            "provenance": d["provenance"],
                            "source_doc": d.get("source_doc"),
                        }
                    )
                    if other not in seen_nodes:
                        seen_nodes.add(other)
                        nxt.add(other)
            frontier = nxt
        nodes = [
            {"id": nid, **{k: v for k, v in self.g.nodes[nid].items() if k != "id"}}
            for nid in sorted(seen_nodes)
        ]
        return {"nodes": nodes, "edges": seen_edges}

    def shortest_path(self, source_id: str, target_id: str) -> Optional[list[str]]:
        try:
            undirected = self.g.to_undirected()
            return nx.shortest_path(undirected, source_id, target_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound, KeyError):
            return None

    def triples(self, node_id: str, relation: Optional[str] = None) -> list[dict]:
        out = []
        if node_id not in self.g:
            return out
        for u, v, d in self.g.out_edges(node_id, data=True):
            if relation in (None, d["relation"]):
                out.append({"source": u, "relation": d["relation"], "target": v, **{k: d.get(k) for k in ("provenance", "source_doc")}})
        for u, v, d in self.g.in_edges(node_id, data=True):
            if relation in (None, d["relation"]):
                out.append({"source": u, "relation": d["relation"], "target": v, **{k: d.get(k) for k in ("provenance", "source_doc")}})
        return out

    def citable_triples(self, node_id: str) -> list[dict]:
        """Triples that may be used as primary facts (non-INFERRED only)."""
        return [t for t in self.triples(node_id) if t.get("provenance") != "INFERRED"]

    # -- stats ---------------------------------------------------------------

    def stats(self) -> dict:
        return {
            "nodes": self.g.number_of_nodes(),
            "edges": self.g.number_of_edges(),
            "meta": self.meta,
        }
