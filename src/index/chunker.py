"""Header-aware deterministic Markdown chunker for the approved knowledge base.

Creates indexable chunks: one for the document preamble and one per "##"
heading section. Chunk IDs and content hashes are deterministic, so indexes
reproducibly rebuild from the same approved corpus (Constitution P7).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.governance.validator import extract_frontmatter, validate_markdown_file

_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    doc_path: str
    category: str
    title: str
    heading: str
    url: str
    text: str
    content_hash: str
    effective_academic_year: str
    review_before_date: Optional[str]
    keywords: list[str] = field(default_factory=list)

    @property
    def searchable_text(self) -> str:
        """Chunk body plus frontmatter keyword expansion for synonym recall."""
        kw = " ".join(self.keywords)
        return f"{self.heading}\n{self.text}\n{kw}".strip()

    @property
    def citation(self) -> str:
        return f"[Source: {self.doc_path} > {self.heading} ({self.url})]"


def _chunk_id(doc_id: str, heading: str, index: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-") or "section"
    return f"{doc_id}::{slug}::{index}"


def chunk_markdown_file(file_path: str | Path) -> list[Chunk]:
    path = Path(file_path)
    result = validate_markdown_file(str(path))
    if not result.is_valid or result.frontmatter is None:
        raise ValueError(f"Cannot chunk invalid document {path}: {result.errors}")
    fm = result.frontmatter
    _, body, _ = extract_frontmatter(path.read_text(encoding="utf-8"))

    chunks: list[Chunk] = []
    matches = list(_HEADING_RE.finditer(body))
    # Preamble chunk (everything before first ##, i.e. the document intro/title).
    intro_end = matches[0].start() if matches else len(body)
    intro = body[:intro_end].replace(f"# {fm.title}", "", 1).strip()
    if intro:
        chunks.append(_make_chunk(fm, str(path), "Introduction", intro, 0))

    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        section_text = body[start:end].strip()
        if section_text:
            chunks.append(_make_chunk(fm, str(path), heading, section_text, i + 1))
    return chunks


def _make_chunk(fm, doc_path: str, heading: str, text: str, index: int) -> Chunk:
    chunk_id = _chunk_id(fm.id, heading, index)
    full_text = f"{heading}\n{text}"
    digest = hashlib.md5(full_text.encode("utf-8")).hexdigest()
    return Chunk(
        chunk_id=chunk_id,
        doc_id=fm.id,
        doc_path=doc_path.replace("\\", "/"),
        category=fm.category.value,
        title=fm.title,
        heading=heading,
        url=fm.official_url,
        text=text,
        content_hash=digest,
        effective_academic_year=fm.effective_academic_year,
        review_before_date=(
            fm.review_before_date.isoformat() if fm.review_before_date else None
        ),
        keywords=list(fm.keywords),
    )


def chunk_directory(dir_path: str | Path) -> list[Chunk]:
    """Chunk every valid approved document in a directory tree."""
    chunks: list[Chunk] = []
    corpus = sorted(Path(dir_path).rglob("*.md"))
    for md in corpus:
        try:
            chunks.extend(chunk_markdown_file(md))
        except ValueError:
            continue  # invalid records never enter indexes
    return chunks
