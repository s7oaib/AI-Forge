"""Settings, read from environment variables (and an optional .env file)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent

# Values in .env are used only when the variable is not already set in the shell.
load_dotenv(PROJECT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    llm_provider: str   # "anthropic" or "offline"
    model: str
    knowledge_dir: Path
    host: str
    port: int

    @property
    def llm_requested(self) -> bool:
        return self.llm_provider == "anthropic"


def load_settings() -> Settings:
    knowledge_dir = Path(os.getenv("KNOWLEDGE_DIR", "knowledge"))
    if not knowledge_dir.is_absolute():
        knowledge_dir = PROJECT_DIR / knowledge_dir
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "offline").strip().lower(),
        model=os.getenv("CHATBOT_MODEL", "claude-opus-5-5").strip(),
        knowledge_dir=knowledge_dir,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
    )
