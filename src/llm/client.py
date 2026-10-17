"""Pluggable LLM provider abstraction (ADR-001).

Only two families exist by design:
- OllamaProvider: local Ollama daemon (privacy-first default candidate)
- HostedProvider: approved hosted APIs (Anthropic by default)
Fallback: provider=None => deterministic retrieval-only answers.
"""

from __future__ import annotations

import os
from typing import Optional, Protocol


class LLMProvider(Protocol):
    name: str

    def is_available(self) -> bool: ...

    def generate(self, system: str, user: str, temperature: float = 0.1) -> str: ...


class OllamaProvider:
    name = "ollama"

    def __init__(self, base_url: Optional[str] = None, model: str = "llama3.1:8b"):
        self.base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            import httpx  # type: ignore

            return httpx.get(f"{self.base_url}/api/tags", timeout=2).status_code == 200
        except Exception:
            return False

    def generate(self, system: str, user: str, temperature: float = 0.1) -> str:
        import httpx  # type: ignore
        import json as _json

        resp = httpx.post(
            f"{self.base_url}/api/generate",
            content=_json.dumps(
                {
                    "model": self.model,
                    "system": system,
                    "prompt": user,
                    "stream": False,
                    "options": {"temperature": temperature},
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["response"]


class HostedProvider:
    name = "hosted"

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or os.environ.get("HOSTED_LLM_MODEL", "claude-3-5-sonnet-latest")
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, system: str, user: str, temperature: float = 0.1) -> str:
        import anthropic  # type: ignore

        client = anthropic.Anthropic(api_key=self.api_key)
        msg = client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=temperature,
        )
        return "".join(block.text for block in msg.content if block.type == "text")


def make_provider(kind: Optional[str] = None, **kwargs) -> Optional[LLMProvider]:
    kind = kind or os.environ.get("COLLEGE_CHATBOT_LLM_PROVIDER", "none")
    if kind == "ollama":
        return OllamaProvider(**kwargs)
    if kind == "hosted":
        return HostedProvider(**kwargs)
    return None
