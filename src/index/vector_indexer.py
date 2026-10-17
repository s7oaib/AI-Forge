"""ChromaDB-backed dense vector store with pluggable embedding providers (ADR-002).

Embedding backends:
- DeterministicHashEmbedder (default): offline, deterministic hashed-ngram
  vectors with L2 normalization -> enables reproducible tests without network.
- SentenceTransformerEmbedder / HttpEmbedder: optional local or hosted
  models, activated when configured.

Storage backends:
- ChromaBackend when `chromadb` is importable (persist_dir artifacts/vector_index).
- NumpyBackend fallback: cosine similarity over a persisted npz matrix.
"""

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from typing import Iterable, Optional, Protocol

import numpy as np

from src.index.chunker import Chunk

DEFAULT_DIR = "artifacts/vector_index"
DIM = 384

_WORD_RE = re.compile(r"[a-z0-9]+")

_SUFFIXES = ("ing", "ies", "ied", "ed", "es", "s")


def _stem(token: str) -> str:
    """Crude deterministic stemmer so morphological variants share hash slots."""
    for suf in _SUFFIXES:
        if len(token) > 4 and token.endswith(suf):
            return token[: -len(suf)]
    return token


# ---------------------------------------------------------------- embeddings

class EmbeddingProvider(Protocol):
    name: str

    def embed(self, text: str) -> np.ndarray: ...


def _l2(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v


def _tokenize(text: str) -> list[str]:
    return [_stem(t) for t in _WORD_RE.findall(text.lower())]


class DeterministicHashEmbedder:
    name = "deterministic-hash"

    def embed(self, text: str) -> np.ndarray:
        v = np.zeros(DIM, dtype="float32")
        tokens = _tokenize(text)
        grams = tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
        for g in grams:
            h = hashlib.md5(g.encode("utf-8")).digest()
            idx = int.from_bytes(h[:4], "little") % DIM
            sign = 1.0 if h[4:6][0] % 2 else -1.0
            v[idx] += sign
        return _l2(v)


class SentenceTransformerEmbedder:
    """Optional local embedder: sentence-transformers must be installed."""

    name = "sentence-transformers"

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer  # type: ignore

        self.model = SentenceTransformer(model)

    def embed(self, text: str) -> np.ndarray:
        vec = self.model.encode(text, normalize_embeddings=True)
        return np.asarray(vec, dtype="float32")


class OpenAIEmbedder:
    """Optional hosted embedder via an OpenAI-compatible HTTP API."""

    name = "openai"

    def __init__(self, model: str = "text-embedding-3-small", base_url: str = "https://api.openai.com/v1", api_key: str = ""):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def embed(self, text: str) -> np.ndarray:
        try:
            import httpx  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("httpx required for OpenAIEmbedder") from e
        resp = httpx.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": text},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()["data"][0]["embedding"]
        return np.asarray(data, dtype="float32")


def make_embedder(kind: str = "deterministic", **kwargs) -> EmbeddingProvider:
    if kind == "deterministic":
        return DeterministicHashEmbedder()
    if kind == "sentence-transformers":
        return SentenceTransformerEmbedder(**kwargs)
    if kind == "openai":
        return OpenAIEmbedder(**kwargs)
    raise ValueError(f"Unknown embedder kind: {kind}")


# -------------------------------------------------------------------- stores

class VectorStore(Protocol):
    backend: str

    def upsert(self, ids: list[str], vectors: list[np.ndarray], metas: list[dict]) -> None: ...
    def delete(self, ids: list[str]) -> None: ...
    def query(self, vector: np.ndarray, k: int) -> list[dict]: ...
    def count(self) -> int: ...


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class NumpyBackend:
    backend = "numpy"

    def __init__(self, persist_dir: str | Path = DEFAULT_DIR):
        self.dir = Path(persist_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._ids: list[str] = []
        self._vectors: np.ndarray = np.zeros((0, DIM), dtype="float32")
        self._metas: dict[str, dict] = {}
        self._reload()

    def _reload(self) -> None:
        vec_file = self.dir / "vectors.npz"
        meta_file = self.dir / "meta.json"
        if vec_file.exists():
            data = np.load(vec_file, allow_pickle=False)
            self._vectors = data["vectors"]
            self._ids = list(data["ids"])
            import json

            self._metas = json.loads(meta_file.read_text("utf-8")) if meta_file.exists() else {}

    def _flush(self) -> None:
        np.savez(self.dir / "vectors.npz", ids=np.asarray(self._ids), vectors=self._vectors)
        import json

        (self.dir / "meta.json").write_text(json.dumps(self._metas), "utf-8")

    def upsert(self, ids, vectors, metas) -> None:
        existing = {cid: i for i, cid in enumerate(self._ids)}
        for cid, vec, meta in zip(ids, vectors, metas):
            if cid in existing:
                self._vectors[existing[cid]] = vec
            else:
                existing[cid] = len(self._ids)
                self._ids.append(cid)
                self._vectors = (
                    np.vstack([self._vectors, vec.reshape(1, -1)])
                    if self._vectors.shape[0]
                    else vec.reshape(1, -1)
                )
            self._metas[cid] = meta
        self._flush()

    def delete(self, ids: list[str]) -> None:
        keep = [i for i, cid in enumerate(self._ids) if cid not in set(ids)]
        removed = [cid for cid in self._ids if cid in set(ids)]
        self._ids = [self._ids[i] for i in keep]
        self._vectors = self._vectors[keep] if keep else np.zeros((0, DIM), dtype="float32")
        for cid in removed:
            self._metas.pop(cid, None)
        self._flush()

    def query(self, vector: np.ndarray, k: int) -> list[dict]:
        if not self._ids:
            return []
        sims = np.asarray([_cosine(vector, vec) for vec in self._vectors])
        order = np.argsort(-sims)[:k]
        return [
            {
                "chunk_id": self._ids[int(i)],
                "similarity": float(sims[int(i)]),
                **self._metas.get(self._ids[int(i)], {}),
            }
            for i in order
        ]

    def count(self) -> int:
        return len(self._ids)


class InMemoryBackend:
    backend = "memory"

    def __init__(self):
        self._ids: list[str] = []
        self._vectors: np.ndarray = np.zeros((0, DIM), dtype="float32")
        self._metas: dict[str, dict] = {}

    def upsert(self, ids, vectors, metas) -> None:
        existing = {cid: i for i, cid in enumerate(self._ids)}
        for cid, vec, meta in zip(ids, vectors, metas):
            if cid in existing:
                self._vectors[existing[cid]] = vec
            else:
                existing[cid] = len(self._ids)
                self._ids.append(cid)
                self._vectors = (
                    np.vstack([self._vectors, vec.reshape(1, -1)])
                    if self._vectors.shape[0]
                    else vec.reshape(1, -1)
                )
            self._metas[cid] = meta

    def delete(self, ids: list[str]) -> None:
        keep = [i for i, cid in enumerate(self._ids) if cid not in set(ids)]
        removed = [cid for cid in self._ids if cid in set(ids)]
        self._ids = [self._ids[i] for i in keep]
        self._vectors = self._vectors[keep] if keep else np.zeros((0, DIM), dtype="float32")
        for cid in removed:
            self._metas.pop(cid, None)

    def query(self, vector: np.ndarray, k: int) -> list[dict]:
        if not self._ids:
            return []
        sims = np.asarray([_cosine(vector, vec) for vec in self._vectors])
        order = np.argsort(-sims)[:k]
        return [
            {
                "chunk_id": self._ids[int(i)],
                "similarity": float(sims[int(i)]),
                **self._metas.get(self._ids[int(i)], {}),
            }
            for i in order
        ]

    def count(self) -> int:
        return len(self._ids)


class ChromaBackend:
    backend = "chroma"

    def __init__(self, persist_dir: str | Path = DEFAULT_DIR):
        import chromadb  # type: ignore

        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.collection = self.client.get_or_create_collection("chunks")

    def upsert(self, ids, vectors, metas) -> None:
        self.collection.upsert(
            ids=ids,
            embeddings=[v.tolist() for v in vectors],
            metadatas=metas,
        )

    def delete(self, ids: list[str]) -> None:
        if ids:
            self.collection.delete(ids=ids)

    def query(self, vector: np.ndarray, k: int) -> list[dict]:
        res = self.collection.query(query_embeddings=[vector.tolist()], n_results=k)
        out = []
        ids = res.get("ids", [[]])[0]
        for i, cid in enumerate(ids):
            meta = (res.get("metadatas") or [[]])[0][i] if res.get("metadatas") else {}
            sim = float((res.get("distances") or [[0]])[0][i])
            out.append({"chunk_id": cid, "similarity": 1.0 - sim, **meta})
        return out

    def count(self) -> int:
        return self.collection.count()


def _default_backend(persist_dir) -> VectorStore:
    try:
        return ChromaBackend(persist_dir)
    except Exception:
        return NumpyBackend(persist_dir)


class VectorIndex:
    def __init__(
        self,
        embedder: Optional[EmbeddingProvider] = None,
        persist_dir: str | Path = DEFAULT_DIR,
        backend: Optional[VectorStore] = None,
    ):
        self.embedder = embedder or DeterministicHashEmbedder()
        self.store = backend or _default_backend(persist_dir)

    def build(self, chunks: Iterable[Chunk]) -> int:
        chunks = list(chunks)
        ids, vectors, metas = [], [], []
        for c in chunks:
            ids.append(c.chunk_id)
            vectors.append(self.embedder.embed(c.searchable_text))
            metas.append(
                {
                    "doc_id": c.doc_id,
                    "doc_path": c.doc_path,
                    "category": c.category,
                    "heading": c.heading,
                    "url": c.url,
                    "year": c.effective_academic_year,
                    "review_before_date": c.review_before_date,
                }
            )
        self.store.upsert(ids, vectors, metas)
        return len(ids)

    def purge(self, chunk_ids: list[str]) -> None:
        self.store.delete(chunk_ids)

    def count(self) -> int:
        return self.store.count()

    def search(self, query: str, k: int = 5, doc_paths: Optional[set[str]] = None) -> list[dict]:
        import datetime

        vector = self.embedder.embed(query)
        hits = self.store.query(vector, k * 3)  # oversample for post-filters
        if doc_paths:
            hits = [h for h in hits if h.get("doc_path") in doc_paths]
        today = datetime.date.today().isoformat()
        hits = [h for h in hits if not h.get("review_before_date") or h["review_before_date"] >= today]
        return hits[:k]
