import shutil
from pathlib import Path

import pytest

from app import create_app
from chatbot.answer import ChatEngine
from chatbot.config import Settings

PROJECT_DIR = Path(__file__).resolve().parent.parent
REAL_KNOWLEDGE = PROJECT_DIR / "knowledge"


@pytest.fixture
def knowledge_copy(tmp_path):
    """A private copy of the real knowledge files that a test may edit."""
    target = tmp_path / "knowledge"
    shutil.copytree(REAL_KNOWLEDGE, target)
    return target


@pytest.fixture
def engine():
    """Offline engine over the real knowledge files (no LLM, no network)."""
    return ChatEngine(REAL_KNOWLEDGE, model="test-model", llm_enabled=False)


@pytest.fixture
def client(engine):
    settings = Settings(llm_provider="offline", model="test-model",
                        knowledge_dir=REAL_KNOWLEDGE, host="127.0.0.1", port=0)
    app = create_app(settings, engine)
    app.testing = True
    return app.test_client()
