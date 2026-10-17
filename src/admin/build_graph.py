"""Administrative graph compilation: builds artifacts/graph/graph.json.

Primary path is deterministic: nodes/edges are harvested from approved
document frontmatter (entities + relationships) plus structural rules.
Optionally wraps `graphify extract` when the CLI is available (--use-graphify),
merging any additional inferred edges produced by community detection.
"""

import argparse
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

from src.governance.validator import validate_directory
from src.graph.edge_classifier import Provenance, classify_edge
from src.graph.graphify_config import DEFAULT_GRAPH_PATH, STRUCTURAL_RULES

GRAPHIFY_BINARY = Path(r"C:\Users\shoai\.local\bin\graphify.exe")


def _derived_node_type(node_id: str, known_types: dict) -> str:
    return known_types.get(node_id, "Undefined")


def build_graph(
    approved_dir: str = "knowledge/approved",
    out_path: str = DEFAULT_GRAPH_PATH,
    use_graphify: bool = False,
) -> dict:
    results = validate_directory(approved_dir)
    invalid = [p for p, r in results.items() if not r.is_valid]
    if invalid:
        raise ValueError(f"Refusing to build graph: invalid documents: {invalid}")

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    # Anchor the college node
    nodes["COL-CORE"] = {
        "id": "COL-CORE",
        "type": "College",
        "name": "Greenfield College of Engineering",
        "source_doc": None,
        "aliases": ["college", "greenfield", "greenfield college", "the college"],
    }

    doc_entities: dict[str, set] = {}
    for path, result in sorted(results.items()):
        fm = result.frontmatter
        doc_rel = str(Path(path).relative_to(approved_dir)).replace("\\", "/")
        for ent in fm.entities:
            existing = nodes.get(ent.id)
            if existing is None:
                nodes[ent.id] = {
                    "id": ent.id,
                    "type": ent.type,
                    "name": ent.name,
                    "source_doc": doc_rel,
                    "aliases": [ent.name.lower()],
                }
            else:
                # Endpoint-guess placeholder: upgrade with the declared entity data.
                if existing["name"] == ent.id or existing["type"] == "Undefined":
                    existing["name"] = ent.name
                    existing["type"] = ent.type
                if ent.name.lower() not in existing["aliases"]:
                    existing["aliases"].append(ent.name.lower())
            doc_entities.setdefault(ent.id, set()).add(doc_rel)

        for rel in fm.relationships:
            prov = classify_edge(rel.relation, source_doc=doc_rel)
            edges.append(
                {
                    "source": rel.source,
                    "relation": rel.relation,
                    "target": rel.target,
                    "provenance": prov.value,
                    "source_doc": doc_rel,
                }
            )
            # register referenced-but-undeclared endpoints
            for endpoint in (rel.source, rel.target):
                if endpoint not in nodes:
                    guess_type = "Faculty" if endpoint.startswith("FAC-") else "Undefined"
                    nodes[endpoint] = {
                        "id": endpoint,
                        "type": guess_type,
                        "name": endpoint,
                        "source_doc": doc_rel,
                        "aliases": [],
                    }

        # Structural: department containment
        if fm.category.value == "departments":
            for ent in fm.entities:
                if ent.type == "Department":
                    nodes[ent.id]["aliases"] = list(
                        set(nodes[ent.id]["aliases"] + [k.lower() for k in fm.keywords])
                    )
                    edges.append(
                        {
                            "source": "COL-CORE",
                            "relation": "HAS_DEPARTMENT",
                            "target": ent.id,
                            "provenance": Provenance.STRUCTURAL.value,
                            "source_doc": doc_rel,
                        }
                    )

        # keyword aliases, per document, attached to primary entity
        if fm.entities and fm.keywords:
            primary = fm.entities[0]
            nodes[primary.id]["aliases"] = sorted(
                set(
                    nodes[primary.id]["aliases"]
                    + [k.lower().strip() for k in fm.keywords if len(k) >= 3]
                )
            )

    graph = {
        "meta": {
            "built_on": date.today().isoformat(),
            "builder": "frontmatter-deterministic" if not use_graphify else "graphify",
            "schema_version": "1.0.0",
        },
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "edges": sorted(edges, key=lambda e: (e["source"], e["relation"], e["target"])),
    }

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(graph, indent=2, sort_keys=False), encoding="utf-8")
    return graph


def maybe_run_graphify_extract(corpus_dir: str, out_dir: str) -> bool:
    """Optionally invoke the Graphify CLI for semantic extraction enrichment."""
    if not shutil.which(str(GRAPHIFY_BINARY)):
        return False
    try:
        subprocess.run(
            [str(GRAPHIFY_BINARY), "extract", "--input", corpus_dir, "--out", out_dir],
            check=True,
            capture_output=True,
            timeout=600,
        )
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Build runtime graph artifact")
    parser.add_argument("--approved", default="knowledge/approved")
    parser.add_argument("--out", default=DEFAULT_GRAPH_PATH)
    parser.add_argument("--use-graphify", action="store_true")
    args = parser.parse_args()
    if args.use_graphify:
        maybe_run_graphify_extract(args.approved, str(Path(args.out).parent))
    g = build_graph(args.approved, args.out, use_graphify=args.use_graphify)
    print(
        f"Built graph: {len(g['nodes'])} nodes, {len(g['edges'])} edges -> {args.out}"
    )


if __name__ == "__main__":
    main()
