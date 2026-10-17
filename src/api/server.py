"""FastAPI REST query service (T031 / ADR-006).

Endpoints:
- POST /api/v1/query  {"message": "...", "history": [...]}
- GET  /api/v1/health
- GET /w/{anything}   -> serves the embeddable chat widget demo page
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator

from src.core.log_sanitizer import sanitize_for_log
from src.llm.client import make_provider
from src.rag.pipeline import QueryPipeline

logger = logging.getLogger("college-chatbot.api")
QUERY_PATH = "/api/v1/query"
HEALTH_PATH = "/api/v1/health"

pipeline: Optional[QueryPipeline] = None
app = FastAPI(title="College Information Chatbot", version="1.0.0", docs_url="/api/docs")


class QueryRequest(BaseModel):
    message: str = Field(..., description="User question")
    history: Optional[list] = Field(None, description="Optional [{role, content}] list")

    @field_validator("message")
    @classmethod
    def message_nonempty(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError("message must be a non-empty question")
        if len(v) > 1000:
            raise ValueError("message exceeds 1000 characters")
        return v


class QueryResponse(BaseModel):
    answer: str
    mode: str
    abstained: bool = False
    sources: list[dict] = []
    confidence: float = 0.0


def get_pipeline() -> QueryPipeline:
    global pipeline
    if pipeline is None:
        pipeline = QueryPipeline(llm=make_provider())
    return pipeline


def set_pipeline(p: QueryPipeline) -> None:
    global pipeline
    pipeline = p


@app.post(QUERY_PATH, response_model=QueryResponse)
def query(req: QueryRequest):
    try:
        p = get_pipeline()
        result = p.answer(req.message, req.history)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # defensive: user-facing failure must not leak internals
        logger.exception("query failure: %s", e)
        raise HTTPException(status_code=500, detail="Internal error while answering")
    logger.info(
        "query mode=%s conf=%.3f sources=%d msg=%s",
        result.mode,
        result.confidence,
        len(result.sources),
        sanitize_for_log(req.message[:80]),
    )
    return QueryResponse(
        answer=result.answer,
        mode=result.mode,
        abstained=result.abstained,
        sources=result.sources,
        confidence=result.confidence,
    )


@app.get(HEALTH_PATH)
def health():
    p = get_pipeline()
    return {
        "status": "ok",
        "graph_nodes": p.graph.stats()["nodes"],
        "graph_edges": p.graph.stats()["edges"],
        "bm25_chunks": p.bm25.count(),
    }


WIDGET_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Greenfield College Chatbot</title>
<script src="/static/chat_widget.js" data-endpoint="/api/v1/query"></script>
</head><body style="margin:0;background:#0f172a;color:#e2e8f0;font-family:sans-serif">
<div style="padding:24px"><h1>Greenfield College Assistant</h1>
<p>This page embeds the chat widget below. You may also call
<code>POST /api/v1/query</code> directly.</p></div></body></html>"""


@app.get("/")
def index():
    return HTMLResponse(WIDGET_PAGE)
