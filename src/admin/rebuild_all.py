"""Deterministic full-rebuild CLI (T037): validate -> graph -> chunk -> index.

Run:  python -m src.admin.rebuild_all [--approve-docs] [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Optional

from src.admin.build_graph import main as build_graph_main
from src.governance.validator import validate_directory
from src.index.bm25_indexer import BM25Index
from src.index.chunker import chunk_directory
from src.index.vector_indexer import VectorIndex, make_embedder

ARTIFACTS = Path("artifacts")


def _artifact_checksums() -> dict:
    checksums = {}
    for f in sorted(ARTIFACTS.rglob("*")):
        if f.is_file():
            checksums[str(f)] = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
    return checksums


def rebuild(verbose: bool = False) -> dict:
    report: dict = {}

    # 1. governance validation gate
    print("[1/4] Validating approved corpus...")
    results = validate_directory(Path("knowledge/approved"))
    failures = [p for p, r in results.items() if not r.is_valid]
    report["validated_documents"] = len(results)
    report["validation_failures"] = len(failures)
    if failures:
        for p in failures:
            print(f"  INVALID {p}: {results[p].errors}")
        raise SystemExit("Rebuild aborted: invalid documents present.")

    # 2. graph build
    print("[2/4] Building knowledge graph...")
    build_graph_main()
    report["graph_built"] = True

    # 3. chunking + lexical/dense indexes
    print("[3/4] Chunking + rebuilding indexes...")
    chunks = chunk_directory(Path("knowledge/approved"))
    bm25 = BM25Index(":memory:")
    n_lexical = bm25.build(chunks)
    vector = VectorIndex(embedder=make_embedder())
    n_dense = vector.build(chunks)
    report["lexical_index_entries"] = n_lexical
    report["dense_index_entries"] = n_dense

    # 4. checksums
    print("[4/4] Computing artifact checksums...")
    report["checksums"] = _artifact_checksums()

    with open(ARTIFACTS / "rebuild_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != "checksums"}, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Full deterministic rebuild")
    args = parser.parse_args()
    rebuild()
