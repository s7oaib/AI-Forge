"""Unified query pipeline: retrieve, fuse, gate, generate, validate (T025+T030 hookup)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.core.log_sanitizer import sanitize_for_log
from src.graph.adapter import GraphAdapter
from src.index.bm25_indexer import BM25Index
from src.index.chunker import Chunk, chunk_directory
from src.index.vector_indexer import DeterministicHashEmbedder, InMemoryBackend, VectorIndex
from src.llm.prompts import ABSTAIN_SENTENCE, SYSTEM_CONSTITUTION, build_user_prompt
from src.llm.validator import validate_citations
from src.rag.abstention_gate import evaluate
from src.rag.context_builder import ContextBuilder
from src.rag.entity_linker import EntityLinker
from src.rag.graph_retriever import GraphRetriever
from src.rag.safety_guard import classify_request, refusal, sanitize_for_retrieval


@dataclass
class AnswerResult:
    answer: str
    mode: str  # "llm" | "retrieval" | "abstain" | "input_error"
    abstained: bool = False
    confidence: float = 0.0
    sources: list[dict] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)


MAX_INPUT_LEN = 1000


class QueryPipeline:
    """End-to-end constitutional query engine.

    Loads approved corpus + derived artifacts at boot. Stale chunks are
    dropped at runtime; staging content never enters this path.
    """

    def __init__(
        self,
        corpus_dir: str | Path = "knowledge/approved",
        graph_path: str | Path = "artifacts/graph/graph.json",
        llm=None,
        hop: int = 2,
    ):
        self.corpus_dir = Path(corpus_dir)
        self.llm = llm
        self.hop = hop
        self.reload(corpus_dir, graph_path)

    def reload(self, corpus_dir: Optional[str | Path] = None, graph_path: Optional[str | Path] = None) -> None:
        corpus_dir = corpus_dir or self.corpus_dir
        graph_path = graph_path or "artifacts/graph/graph.json"
        self.graph = GraphAdapter.load(graph_path)
        chunks = chunk_directory(corpus_dir)
        self.bm25 = BM25Index(":memory:")
        self.bm25.build(chunks)
        self.vector = VectorIndex(embedder=DeterministicHashEmbedder(), backend=InMemoryBackend())
        self.vector.build(chunks)
        self.linker = EntityLinker(self.graph)
        self.retriever = GraphRetriever(self.graph, hop=self.hop)
        self.context_builder = ContextBuilder()
        self._corpus_path = str(corpus_dir)

    # ---------------------------------------------------------------- answer

    def answer(self, question: str, history: Optional[list] = None) -> AnswerResult:
        trace: list[str] = []
        if not isinstance(question, str) or not question.strip():
            return AnswerResult(
                answer="Please ask a question about the college.",
                mode="input_error",
                trace=["empty or invalid input rejected"],
            )
        question = question.strip()
        if len(question) > MAX_INPUT_LEN:
            return AnswerResult(
                answer="That question is too long. Please ask a shorter question.",
                mode="input_error",
                trace=["input exceeds 1000 chars rejected"],
            )

        trace.append(f"answer(question={sanitize_for_log(question[:120])})")

        category = classify_request(question)
        if category:
            trace.append(f"security_dice=refused ({category})")
            return AnswerResult(
                answer=refusal(category),
                mode="abstain",
                abstained=True,
                trace=trace,
            )

        question = sanitize_for_retrieval(question)

        # 1-4 lexical + dense retrieval and evidence assembly over approved corpus
        bm_hits = self.bm25.search(question, k=8)
        vs_hits = self.vector.search(question, k=8)
        trace.append(f"lexical_candidates={len(bm_hits)} dense_candidates={len(vs_hits)}")

        chunk_ids = list(dict.fromkeys([h["chunk_id"] for h in bm_hits] + [h["chunk_id"] for h in vs_hits]))
        chunk_map = {}
        if chunk_ids:
            marks = ",".join("?" * len(chunk_ids))
            rows = self.bm25.conn.execute(
                f"SELECT chunk_id FROM chunks WHERE chunk_id IN ({marks})", chunk_ids
            ).fetchall()
            chunk_map = {r[0] for r in rows}

        # graph evidence
        linked = self.linker.link(question)
        trace.append(f"linked_entities={[l['node_id'] for l in linked]}")
        sub = self.retriever.extract([l["node_id"] for l in linked]) if linked else {"nodes": [], "edges": []}
        facts = self.retriever.fact_lines(sub)

        text_hits = {h["chunk_id"]: h for h in (bm_hits[:5] + vs_hits[:5])}
        # de-duplicate preserving order
        ordered_ids = list(dict.fromkeys([h["chunk_id"] for h in bm_hits[:5]] + [h["chunk_id"] for h in vs_hits[:5]]))
        ordered = [text_hits[cid] for cid in ordered_ids if cid in text_hits]
        ordered = [h for h in ordered if h.get("doc_path")]

        # real chunk objects for context building (we re-chunk lazily via bm cache)
        chunk_objs = self._chunk_lookup(ordered_ids)

        fused_scores = {}
        from src.rag.rrf import rrf_fuse

        fused_scores = rrf_fuse(
            [[h["chunk_id"] for h in bm_hits[:5]], [h["chunk_id"] for h in vs_hits[:5]]]
        )
        confidence = 0.0
        if fused_scores:
            from src.rag.rrf import normalize

            confidence = normalize(fused_scores)

        # Need SOME textual evidence; graph-only queries must at least have a chunk.
        has_lexical_support = bool(bm_hits)
        has_structural_support = bool(linked)
        if not has_lexical_support and not has_structural_support:
            trace.append("abstention_gate=BLOCKED (no lexical or structural evidence)")
            return AnswerResult(
                answer=ABSTAIN_SENTENCE,
                mode="abstain",
                abstained=True,
                confidence=confidence,
                trace=trace,
            )
        if not chunk_objs and facts:
            evidence_chunks = []
        else:
            # temporal re-check on actual chunk objects
            from src.rag.temporal_filter import filter_chunks

            fres = filter_chunks(chunk_objs)
            evidence_chunks = fres.fresh
            for w in fres.warnings:
                trace.append(w)

        ctx = self.context_builder.build(evidence_chunks, sub, facts)
        trace.append(f"context_chunks={len(ctx['chunk_ids'])} graph_facts={len(ctx['graph_facts'])}")

        # 5-6 generation
        if self.llm and self.llm.is_available():
            user_prompt = build_user_prompt(question, ctx["xml"], history)
            raw = self.llm.generate(SYSTEM_CONSTITUTION, user_prompt)
            check = validate_citations(raw, ctx["chunk_ids"], ctx["documents"])
            if not check.ok:
                trace.append(f"citation_validation_failed={check.violations}")
                raw = self._retrieval_only_answer(evidence_chunks, facts, trace)
                check2 = validate_citations(raw, ctx["chunk_ids"], ctx["documents"])
                return AnswerResult(
                    answer=raw,
                    mode="retrieval",
                    confidence=confidence,
                    sources=self._sources(ctx),
                    violations=(check.violations if check.ok else check2.violations),
                    trace=trace,
                )
            return AnswerResult(
                answer=raw,
                mode="llm",
                confidence=confidence,
                sources=self._sources(ctx),
                trace=trace,
            )

        # 7 retrieval-only deterministic fallback
        raw = self._retrieval_only_answer(evidence_chunks, facts, trace)
        return AnswerResult(
            answer=raw,
            mode="retrieval",
            confidence=confidence,
            sources=self._sources(ctx),
            trace=trace,
        )

    # ----------------------------------------------------------------- helpers

    def _chunk_lookup(self, ordered_ids):
        from src.index.chunker import chunk_directory

        if getattr(self, "_chunk_cache", None) is None or self._chunk_cache_for != self._corpus_path:
            all_chunks = chunk_directory(self.corpus_dir)
            self._chunk_cache = {c.chunk_id: c for c in all_chunks}
            self._chunk_cache_for = self._corpus_path
        return [self._chunk_cache[cid] for cid in ordered_ids if cid in self._chunk_cache]

    def _retrieval_only_answer(self, chunks, facts, trace) -> str:
        lines = []
        for c in chunks[:2]:
            body = " ".join(c.text.split())
            lines.append(body[:400])
            if facts:
                lines.append("Related records: " + "; ".join(facts[:4]) + ".")
        if not lines and facts:
            lines.append("Related records: " + "; ".join(facts[:4]) + ".")
        answer = " ".join(lines).strip()
        # attach citation of the first chunk
        src = ""
        if chunks:
            c = chunks[0]
            src = f" [Source: {c.doc_path} > {c.heading} ({c.url})]"
        elif facts:
            node_doc = None
            for line in facts:
                node_doc = self._fact_source_doc(line)
                if node_doc:
                    break
            if node_doc:
                src = f" [Source: {node_doc['path']} > {node_doc['heading']} ({node_doc['url']})]"
        trace.append("mode=retrieval-fallback")
        return f"{answer}{src}".strip()

    def _fact_source_doc(self, fact_line: str):
        """Best-effort document pointer for a graph fact."""
        hits = self.bm25.search(fact_line.split("--")[0].strip()[:60], k=1)
        if hits:
            return {"path": hits[0]["doc_path"], "heading": hits[0]["heading"], "url": hits[0]["url"]}
        return None

    def _sources(self, ctx) -> list[dict]:
        return [
            {"doc_path": d["path"], "heading": d["heading"], "url": d["url"]}
            for d in ctx["documents"]
        ][:5]
