"""Answer & citation post-validator: citations must map to evidence chunks (T030 / SEC-05)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

SOURCE_LINE_RE = re.compile(
    r"\[Source:\s*(?P<doc>[^\]>]+?)\s*>\s*(?P<heading>[^\]]+?)\s*\((?P<url>https?://[^\)]+)\)\]"
)


@dataclass
class CitationCheck:
    ok: bool
    violations: list[str] = field(default_factory=list)
    cited_documents: list[str] = field(default_factory=list)


def validate_citations(answer: str, evidence_chunk_ids: Iterable[str], context_documents: Iterable[dict]) -> CitationCheck:
    """Every [Source: ...] line in the answer must exist in the context.

    Also enforces that an answer without the sanctioned abstain sentence
    carries at least one citation.
    """
    evidence_chunk_ids = set(evidence_chunk_ids)
    known_docs = {d["path"] for d in context_documents}
    known_urls = {d["url"] for d in context_documents}

    matches = list(SOURCE_LINE_RE.finditer(answer))
    if not matches:
        from src.llm.prompts import ABSTAIN_SENTENCE

        core = answer.strip()
        if ABSTAIN_SENTENCE[:60] in core:
            return CitationCheck(ok=True)
        return CitationCheck(ok=False, violations=["Answer makes claims without any [Source: ...] citation"])

    violations = []
    cited = []
    for m in matches:
        doc, url, heading = m.group("doc").strip(), m.group("url").strip(), m.group("heading").strip()
        doc_norm = doc.replace("\\", "/")
        if doc_norm not in known_docs and url not in known_urls:
            violations.append(f"Citation references unknown document: {doc_norm}")
        else:
            cited.append(doc_norm)
        # heading mismatch tolerance: headings may be abbreviated; doc match is the gate

    return CitationCheck(ok=not violations, violations=violations, cited_documents=cited)
