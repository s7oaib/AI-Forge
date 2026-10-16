"""The question-answering pipeline.

    question -> (follow-up? add previous question) -> retrieve passages
             -> LLM writes a grounded answer   (if enabled and working)
             -> or: show the best passage       (offline / fallback)
             -> or: safe "not in the knowledge base" reply

Conversation history only helps interpret follow-up questions. It is never
added to the knowledge base and is never cited as a source.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from . import llm
from .knowledge import Chunk, load_knowledge, snapshot
from .retrieval import Result, Retriever, is_follow_up

log = logging.getLogger(__name__)

MAX_QUESTION_CHARS = 500
MAX_HISTORY_MESSAGES = 8
MAX_HISTORY_CHARS = 2000

NOT_FOUND = "I couldn't find that in the current demo knowledge base, so I won't guess."


class InputError(ValueError):
    """The request itself is invalid (for example, an empty question)."""


def clean_history(history) -> list[dict]:
    """Keep only well-formed recent turns, starting with a user message."""
    if not isinstance(history, list):
        return []
    turns = [
        {"role": m["role"], "content": m["content"].strip()[:MAX_HISTORY_CHARS]}
        for m in history
        if isinstance(m, dict) and m.get("role") in ("user", "assistant")
        and isinstance(m.get("content"), str) and m["content"].strip()
    ][-MAX_HISTORY_MESSAGES:]
    while turns and turns[0]["role"] != "user":
        turns.pop(0)
    return turns


def _source(chunk: Chunk, role: str, score: float | None = None) -> dict:
    return {"file": chunk.source, "heading": chunk.heading, "role": role, "score": score}


class ChatEngine:
    def __init__(self, knowledge_dir: str | Path, model: str, llm_enabled: bool):
        self.knowledge_dir = Path(knowledge_dir)
        self.model = model
        self.llm_enabled = llm_enabled
        self.last_llm_error: str | None = None
        self._lock = threading.Lock()
        self._snapshot = None
        self.reload()

    # ----- knowledge -------------------------------------------------------
    def reload(self) -> None:
        with self._lock:
            self.kb = load_knowledge(self.knowledge_dir)
            self.retriever = Retriever(self.kb.chunks)
            self._snapshot = snapshot(self.knowledge_dir)
            log.info("Loaded %d passages from %d files", len(self.kb.chunks), len(self.kb.files))

    def reload_if_changed(self) -> None:
        """Pick up edits to the Markdown files without restarting the app."""
        if snapshot(self.knowledge_dir) != self._snapshot:
            self.reload()

    def status(self) -> dict:
        self.reload_if_changed()
        llm_ready = self.llm_enabled and llm.is_configured()
        return {
            "mode": "llm" if llm_ready else "offline",
            "llm_provider": "anthropic" if self.llm_enabled else "none",
            "llm_key_present": llm.is_configured(),
            "model": self.model if llm_ready else None,
            "last_llm_error": self.last_llm_error,
            "files": self.kb.files,
            "passages": len(self.kb.chunks),
            "warnings": self.kb.warnings,
        }

    # ----- answering -------------------------------------------------------
    def _fallback(self, notice: str | None = None, context: str | None = None) -> dict:
        """Safe reply when the knowledge base has no supporting evidence."""
        text, sources = NOT_FOUND, []
        help_chunk = next((c for c in self.kb.chunks if "cannot answer" in c.heading.lower()), None)
        if help_chunk:
            text += f"\n\nHere is what you can do instead (from **{help_chunk.source}**):\n\n{help_chunk.text}"
            sources.append(_source(help_chunk, "fallback"))
        return {"answer": text, "grounded": False, "sources": sources, "mode": "retrieval",
                "context_used": context, "notice": notice}

    def _retrieval_answer(self, results: list[Result], context: str | None, notice: str | None = None) -> dict:
        top = results[0]
        text = (f"Here is what the knowledge base says (**{top.chunk.source}**, "
                f"section \"{top.chunk.heading}\"):\n\n{top.chunk.text}")
        sources = [_source(top.chunk, "answer", top.score)]
        sources += [_source(r.chunk, "related", r.score) for r in results[1:]]
        return {"answer": text, "grounded": True, "sources": sources, "mode": "retrieval",
                "context_used": context, "notice": notice}

    def answer(self, question, history=None, use_llm: bool | None = None) -> dict:
        if not isinstance(question, str) or not question.strip():
            raise InputError("Please type a question first.")
        question = question.strip()
        if len(question) > MAX_QUESTION_CHARS:
            raise InputError(f"Please keep questions under {MAX_QUESTION_CHARS} characters.")

        self.reload_if_changed()
        if not self.kb.chunks:
            return self._fallback(notice="The knowledge base is empty or could not be loaded. "
                                         "Check the knowledge/ folder.")

        history = clean_history(history)
        previous = next((m["content"] for m in reversed(history) if m["role"] == "user"), None)
        context = previous if previous and is_follow_up(question) else None

        results = self.retriever.search(question, context=context)

        want_llm = self.llm_enabled if use_llm is None else use_llm
        if not want_llm:
            return self._retrieval_answer(results, context) if results else self._fallback(context=context)

        if not llm.is_configured():
            notice = "LLM mode needs ANTHROPIC_API_KEY. Showing the retrieval-only answer."
            return self._retrieval_answer(results, context, notice) if results else self._fallback(notice, context)

        # Give the LLM the strong matches, or the closest weak ones so it can judge them.
        passages = [r.chunk for r in results] or [r.chunk for r in self.retriever.candidates(question, context)]
        if not passages:
            return self._fallback(context=context)
        try:
            reply = llm.generate_answer(
                self.model, question,
                [{"source": c.source, "heading": c.heading, "text": c.text} for c in passages],
                history,
            )
            self.last_llm_error = None
        except llm.LLMError as exc:
            log.warning("LLM step failed: %s", exc)
            self.last_llm_error = str(exc)
            notice = f"LLM unavailable: {exc} Showing the retrieval-only answer."
            return self._retrieval_answer(results, context, notice) if results else self._fallback(notice, context)

        if not reply["found"] or not reply["sources"]:
            return {**self._fallback(context=context), "mode": "llm"}
        return {
            "answer": reply["answer"],
            "grounded": True,
            "sources": [_source(passages[n - 1], "answer") for n in reply["sources"]],
            "mode": "llm",
            "context_used": context,
            "notice": None,
        }
