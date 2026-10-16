"""Load the Markdown knowledge files and split them into searchable passages.

Each Markdown file is split at its "## " headings. Every heading plus the text
under it becomes one passage (a "chunk"). The file name and heading are kept so
the chatbot can show where an answer came from.

This module only *reads* files. Conversation history never touches it, so the
college facts stay separate from what users type in the chat.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

MAX_FILE_BYTES = 1_000_000  # ignore anything unexpectedly large


@dataclass(frozen=True)
class Chunk:
    source: str   # file name, e.g. "admissions.md"
    title: str    # document title from the "# " heading
    heading: str  # section heading from the "## " heading
    text: str     # section body (Markdown)


@dataclass
class KnowledgeBase:
    directory: Path
    chunks: list[Chunk] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _strip_blockquotes(text: str) -> str:
    # The "> Illustrative demo data" banners are for human readers; they would
    # otherwise add noise words like "demo" and "fictional" to every passage.
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(">"))


def split_markdown(source: str, markdown: str) -> list[Chunk]:
    """Split one Markdown document into chunks at "## " headings."""
    title_match = re.search(r"^#\s+(.+)$", markdown, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else Path(source).stem.replace("_", " ").title()

    chunks: list[Chunk] = []
    heading = title
    body: list[str] = []

    def flush() -> None:
        text = _strip_blockquotes("\n".join(body)).strip()
        if text:
            chunks.append(Chunk(source=source, title=title, heading=heading, text=text))

    for line in markdown.splitlines():
        if line.startswith("## "):
            flush()
            heading, body = line[3:].strip(), []
        elif re.match(r"^#\s", line):
            continue  # document title line
        else:
            body.append(line)
    flush()
    return chunks


def load_knowledge(directory: str | Path) -> KnowledgeBase:
    """Read every *.md file in `directory`. Problems become warnings, not crashes."""
    directory = Path(directory)
    kb = KnowledgeBase(directory=directory)

    if not directory.is_dir():
        kb.warnings.append(f"Knowledge folder not found: {directory}")
        log.warning(kb.warnings[-1])
        return kb

    for path in sorted(directory.glob("*.md")):
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                raise ValueError(f"file is larger than {MAX_FILE_BYTES} bytes")
            markdown = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            kb.warnings.append(f"Skipped {path.name}: {exc}")
            log.warning(kb.warnings[-1])
            continue

        chunks = split_markdown(path.name, markdown)
        if not chunks:
            kb.warnings.append(f"Skipped {path.name}: no readable content")
            log.warning(kb.warnings[-1])
            continue

        kb.files.append(path.name)
        kb.chunks.extend(chunks)

    if not kb.files:
        kb.warnings.append(f"No usable Markdown files in {directory}")
        log.warning(kb.warnings[-1])
    return kb


def snapshot(directory: str | Path) -> tuple:
    """A cheap fingerprint of the folder, used to reload when files are edited."""
    directory = Path(directory)
    if not directory.is_dir():
        return ()
    return tuple(sorted((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in directory.glob("*.md")))
