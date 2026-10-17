"""SQLite FTS5 lexical indexer with BM25 ranking (ADR-003)."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Iterable, Optional

from src.index.chunker import Chunk

DEFAULT_DB_PATH = "artifacts/bm25_index/bm25.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id     TEXT PRIMARY KEY,
    doc_id       TEXT,
    doc_path     TEXT,
    category     TEXT,
    heading      TEXT,
    url          TEXT,
    year         TEXT,
    review_before_date TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
    chunk_id UNINDEXED, text, tokenize='porter'
);
"""


class BM25Index:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._lock = threading.Lock()

    def init_schema(self) -> None:
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def build(self, chunks: Iterable[Chunk]) -> int:
        """Deterministically rebuild the index from the given chunks."""
        self.init_schema()
        with self.conn:
            self.conn.execute("DELETE FROM chunks")
            self.conn.execute("DELETE FROM chunk_fts")
            n = 0
            for c in chunks:
                self.conn.execute(
                    "INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?)",
                    (c.chunk_id, c.doc_id, c.doc_path, c.category, c.heading, c.url, c.effective_academic_year, c.review_before_date),
                )
                self.conn.execute(
                    "INSERT INTO chunk_fts VALUES (?,?)",
                    (c.chunk_id, c.searchable_text),
                )
                n += 1
        return n

    def count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) FROM chunk_fts").fetchone()
        return int(row[0]) if row else 0

    def purge_stale(self, stale_chunk_ids: Iterable[str]) -> int:
        ids = list(stale_chunk_ids)
        with self.conn:
            for cid in ids:
                self.conn.execute("DELETE FROM chunks WHERE chunk_id=?", (cid,))
                self.conn.execute("DELETE FROM chunk_fts WHERE chunk_id=?", (cid,))
        return len(ids)

    def search(
        self,
        query: str,
        k: int = 5,
        doc_paths: Optional[set[str]] = None,
    ) -> list[dict]:
        """BM25-ranked lexical search. Results ordered best-first.

        Results carrying past review_before_date are excluded at runtime
        (Constitution P6: temporal expiry guard).
        """
        import datetime
        import re as _re

        today = datetime.date.today().isoformat()
        from src.rag.safety_guard import normalize_query

        cleaned = normalize_query(query)
        tokens = _re.findall(r"[a-zA-Z0-9]+", cleaned)
        if not tokens:
            return []
        match_expression = " OR ".join(f'"{t}"' for t in tokens)
        sql = """
            SELECT f.chunk_id,
                   c.doc_id, c.doc_path, c.category, c.heading, c.url, c.year,
                   c.review_before_date,
                   bm25(chunk_fts) AS score
            FROM chunk_fts f
            JOIN chunks c ON c.chunk_id = f.chunk_id
            WHERE chunk_fts MATCH ?
              AND (c.review_before_date IS NULL OR c.review_before_date >= ?)
        """
        params: list = [match_expression, today]
        if doc_paths:
            placeholders = ",".join("?" * len(doc_paths))
            sql += f" AND c.doc_path IN ({placeholders})"
            params.extend(sorted(doc_paths))
        sql += " ORDER BY score ASC LIMIT ?"
        params.append(k)
        with self._lock:
            rows = self.conn.execute(sql, params).fetchall()
        results = []
        for r in rows:
            results.append(
                {
                    "chunk_id": r[0],
                    "doc_id": r[1],
                    "doc_path": r[2],
                    "category": r[3],
                    "heading": r[4],
                    "url": r[5],
                    "year": r[6],
                    "review_before_date": r[7],
                    "bm25_score": r[8],
                }
            )
        return results
