"""Optional LLM step: ask Claude to write an answer using ONLY the retrieved passages.

The chatbot works without this module. It is used only when LLM_PROVIDER=anthropic
and an ANTHROPIC_API_KEY is available. Any failure raises LLMError, and the app
falls back to the retrieval-only answer.
"""

from __future__ import annotations

import json
import logging
import os

import anthropic

log = logging.getLogger(__name__)

# Models that accept the server-side refusal fallback ("fallbacks": "default").
FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}

SYSTEM_PROMPT = """You are the College Information Assistant for Greenfield Demo College, \
a fictional college used in a workshop.

Answer the student's latest question using ONLY the numbered knowledge passages provided \
in their message. Rules:
- Never use outside knowledge and never invent facts, numbers, names or dates.
- Earlier chat messages help you understand follow-up questions, but they are NOT a source \
of facts. Only the passages are.
- If the passages do not contain the answer, set "found" to false and say briefly that the \
information is not in the current demo knowledge base.
- Keep answers short and friendly. Use Markdown bullet lists when listing several items.
- In "sources", list the numbers of the passages you actually used."""

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "found": {"type": "boolean"},
        "answer": {"type": "string"},
        "sources": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["found", "answer", "sources"],
    "additionalProperties": False,
}


class LLMError(Exception):
    """A readable reason the LLM step could not be used."""


def is_configured() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(timeout=60.0, max_retries=1)
    return _client


def generate_answer(model: str, question: str, passages: list[dict], history: list[dict]) -> dict:
    """Return {"found": bool, "answer": str, "sources": [passage numbers]}."""
    if not is_configured():
        raise LLMError("No ANTHROPIC_API_KEY is set, so the LLM step is unavailable.")

    evidence = "\n\n".join(
        f"[{i}] ({p['source']} > {p['heading']})\n{p['text']}" for i, p in enumerate(passages, start=1)
    )
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({
        "role": "user",
        "content": f"Knowledge passages:\n\n{evidence}\n\nQuestion: {question}",
    })

    request = dict(
        model=model,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=messages,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": ANSWER_SCHEMA}},
    )
    try:
        if model in FALLBACK_MODELS:
            response = _get_client().beta.messages.create(
                betas=["server-side-fallback-2026-07-01"], fallbacks="default", **request
            )
        else:
            response = _get_client().messages.create(**request)
    except anthropic.AuthenticationError as exc:
        raise LLMError("The Anthropic API rejected the API key (401). Check ANTHROPIC_API_KEY.") from exc
    except anthropic.PermissionDeniedError as exc:
        raise LLMError("The API key is not allowed to use this model (403).") from exc
    except anthropic.NotFoundError as exc:
        raise LLMError(f"Model '{model}' was not found (404). Check CHATBOT_MODEL.") from exc
    except anthropic.RateLimitError as exc:
        raise LLMError("The Anthropic API rate limit was reached (429). Try again shortly.") from exc
    except anthropic.BadRequestError as exc:
        raise LLMError(f"The Anthropic API rejected the request (400): {exc.message}") from exc
    except anthropic.APIStatusError as exc:
        raise LLMError(f"The Anthropic API returned an error ({exc.status_code}).") from exc
    except anthropic.APIConnectionError as exc:
        raise LLMError("Could not connect to the Anthropic API. Check your internet connection.") from exc

    if response.stop_reason == "refusal":
        raise LLMError("The model declined to answer this request.")
    if response.stop_reason == "max_tokens":
        raise LLMError("The model's answer was cut off (max_tokens).")

    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError("The model returned an unreadable answer.") from exc

    valid = [n for n in data.get("sources", []) if isinstance(n, int) and 1 <= n <= len(passages)]
    log.info("LLM answered (model=%s, found=%s, sources=%s)", response.model, data.get("found"), valid)
    return {"found": bool(data.get("found")), "answer": str(data.get("answer", "")).strip(), "sources": valid}
