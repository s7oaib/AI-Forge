"""Interactive administrator CLI: query the chatbot or run governance audits (T032)."""

from __future__ import annotations

import argparse
import sys

from src.llm.client import make_provider
from src.rag.pipeline import QueryPipeline


def run_query_pipeline():
    pipeline = QueryPipeline(llm=make_provider())
    print("Greenfield College Assistant (retrieval/LLM mode). Type 'exit' to quit.")
    while True:
        try:
            question = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break
        result = pipeline.answer(question)
        print(f"bot[{result.mode}]> {result.answer}")
        for s in result.sources:
            print(f"        source: {s['doc_path']} > {s['heading']} ({s['url']})")


def main():
    parser = argparse.ArgumentParser(description="College Chatbot CLI")
    parser.add_argument("--query", "-q", type=str, help="Ask a one-shot question and exit")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive REPL")
    args = parser.parse_args()
    if args.query:
        pipeline = QueryPipeline(llm=make_provider())
        result = pipeline.answer(args.query)
        print(f"[{result.mode}] {result.answer}")
        if result.confidence:
            print(f"confidence={result.confidence:.3f}")
        for v in result.violations:
            print(f"VIOLATION: {v}", file=sys.stderr)
        return
    if args.interactive or not (args.query):
        run_query_pipeline()


if __name__ == "__main__":
    main()
