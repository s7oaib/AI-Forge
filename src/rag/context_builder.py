"""Unified Context Assembler: merges text chunks and graph triples into
isolated <evidence> XML blocks for the constitutional prompt (T025 / SEC-01)."""

from __future__ import annotations

from typing import Iterable, Optional

MAX_CONTEXT_CHARS = 6000


class ContextBuilder:
    def __init__(self, max_chars: int = MAX_CONTEXT_CHARS):
        self.max_chars = max_chars

    def build(
        self,
        chunks: Iterable,
        subgraph: Optional[dict] = None,
        fact_lines: Optional[list[str]] = None,
    ) -> dict:
        """Assemble the evidence payload.

        Returns:
            {"xml": str, "chunk_ids": set, "documents": [{path,url,heading}], "graph_facts": [...]}
        """
        used: set[str] = set()
        documents: list[dict] = []
        blocks: list[str] = []

        for chunk in chunks:
            if chunk.chunk_id in used:
                continue
            used.add(chunk.chunk_id)
            documents.append(
                {"path": chunk.doc_path, "url": chunk.url, "heading": chunk.heading}
            )
            blocks.append(
                f"<chunk id=\"{chunk.chunk_id}\" doc=\"{chunk.doc_path}\" "
                f"heading=\"{chunk.heading}\" url=\"{chunk.url}\" year=\"{chunk.effective_academic_year}\">\n"
                f"{chunk.text}\n</chunk>"
            )

        graph_section = ""
        if fact_lines:
            graph_section = "<graph_facts>\n" + "\n".join(f"- {line}" for line in fact_lines) + "\n</graph_facts>"

        parts = []
        budget = self.max_chars
        for block in blocks:
            if budget <= 0:
                break
            trimmed = block[:budget]
            budget -= len(trimmed)
            parts.append(trimmed)
        if graph_section and budget > 0:
            parts.append(graph_section[:budget])

        xml = "<evidence>\n" + "\n".join(parts) + "\n</evidence>"
        return {
            "xml": xml,
            "chunk_ids": used,
            "documents": documents,
            "graph_facts": fact_lines or [],
        }
