"""Query-side entity extraction and alias matching (T023)."""

from __future__ import annotations

import re
from typing import Optional


def _query_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class EntityLinker:
    def __init__(self, adapter):
        self.adapter = adapter

    def link(self, query: str, max_entities: int = 6) -> list[dict]:
        """Match node aliases/canonical names inside the query text.

        Greedy longest-alias-first matching prevents e.g. 'nlp' shadowing
        'natural language processing'.
        """
        q = query.lower()
        candidates: list[tuple[int, str, str]] = []  # (alias_len, node_id, alias)
        for alias, node_id in self.adapter._alias_index.items():
            if len(alias) < 3 or not alias:
                continue
            # word-boundary-safe substring match
            if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", q):
                candidates.append((len(alias), node_id, alias))
        candidates.sort(reverse=True)
        seen: set[str] = set()
        out = []
        for _, node_id, alias in candidates[: max_entities * 2]:
            if node_id in seen:
                continue
            seen.add(node_id)
            out.append({"node_id": node_id, "matched_alias": alias})
            if len(out) >= max_entities:
                break
        return out

    def question_type(self, query: str) -> Optional[str]:
        """Light touch for downstream prompt assembly hints."""
        q = query.lower()
        tokens = _query_tokens(q)
        if any(t in tokens for t in ("who", "whom", "teacher", "teacher-in-charge", "heads", "head")):
            return "person_lookup"
        if any(t in tokens for t in ("when", "date", "deadline", "start")):
            return "temporal"
        if any(t in tokens for t in ("where", "location", "located")):
            return "location"
        if any(
            t in tokens
            for t in ("fee", "fees", "cost", "salary", "package", "cutoff", "percentage", "percent")
        ):
            return "quantitative"
        if any(t in tokens for t in ("can i", "how do i", "how to", "apply", "documents")):
            return "procedural"
        return "factual"
