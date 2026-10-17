"""Deterministic benchmark runner (T035).

Recall@5 / answer-correctness / abstention-precision over evaluation/benchmark_100.json.
Run:  python evaluation/eval_runner.py [--top-k 5]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.rag.pipeline import QueryPipeline


def run(benchmark_path: str | Path = "evaluation/benchmark_100.json", top_k: int = 5) -> dict:
    data = json.loads(Path(benchmark_path).read_text(encoding="utf-8"))
    questions = data.get("questions", [])
    if not questions:
        return {
            "status": "empty_benchmark",
            "message": "Benchmark fixture is intentionally empty until college admin signs off on question provenance (Constitution P5).",
            "questions_run": 0,
        }

    pipeline = QueryPipeline()
    run_results = []
    recall_hits, correct, abstain_tp, abstain_total = 0, 0, 0, 0

    for q in questions:
        prompt = q["question"]
        result = pipeline.answer(prompt)
        hit_chunk_ids = {
            s.get("chunk_id") for s in (result.trace or [])
        }
        # trace doesn't carry chunk ids; approximate via hit text docs in sources
        source_paths = {s["doc_path"] for s in result.sources}
        expected = set(q.get("expected_documents", []))
        recall = len(source_paths & expected) / len(expected) if expected else None

        hit = recall is not None and recall >= 1.0
        if hit:
            recall_hits += 1
        correct_response: bool
        if q.get("should_abstain"):
            abstain_total += 1
            correct_response = result.abstained
            if result.abstained:
                abstain_tp += 1
        else:
            correct_response = not result.abstained and hit

        run_results.append(
            {
                "id": q.get("id"),
                "question": prompt,
                "abstained": result.abstained,
                "recall": recall,
                "correct": correct_response,
            }
        )

    total = len(run_results)
    return {
        "questions_run": total,
        "recall_at_5": round(recall_hits / total, 3) if total else 0.0,
        "answer_correctness": round(
            sum(1 for r in run_results if r["correct"]) / total, 3
        )
        if total
        else 0.0,
        "abstention_rate_on_unanswerable": round(abstain_tp / abstain_total, 3)
        if abstain_total
        else None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", default="evaluation/benchmark_100.json")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(run(args.benchmark, args.top_k), indent=2))
