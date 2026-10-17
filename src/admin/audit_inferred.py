"""Audit sample CLI: verify INFERRED edges never ground primary answers (P4)."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from src.graph.adapter import GraphAdapter


def _all_edges() -> list:
    data = json.loads(Path("artifacts/graph/graph.json").read_text(encoding="utf-8"))
    return data["edges"]


def main(sample_size: int = 50) -> None:
    GraphAdapter.load("artifacts/graph/graph.json")  # validates load-ability
    edges = _all_edges()
    citable = [e for e in edges if e["provenance"] != "INFERRED"]
    inferred = [e for e in edges if e["provenance"] == "INFERRED"]
    rng = random.Random(42)
    sample = rng.sample(
        sorted(edges, key=lambda e: (e["source"], e["relation"], e["target"])),
        min(sample_size, len(edges)),
    )

    leaked = [
        e for e in sample
        if e["provenance"] == "INFERRED" and e.get("used_to_ground_primary_fact")
    ]
    report = {
        "sample_size": len(sample),
        "citable_edges": len(citable),
        "inferred_edges": len(inferred),
        "p4_violations": len(leaked),
    }
    print(json.dumps(report, indent=2))
    if leaked:
        raise SystemExit("FAILED: INFERRED edge marked as primary grounding found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=50)
    args = parser.parse_args()
    main(args.sample_size)
