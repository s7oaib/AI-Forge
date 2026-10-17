# Administrator & Operator Guide — Greenfield College Assistant

**Release candidate:** v1.0.0-rc1 · **Python:** 3.11+ · **Runtime deps:** FastAPI, Uvicorn, Pydantic, NetworkX, SQLite (FTS5), NumPy, httpx

## 1. System Overview

The chatbot answers college questions strictly from **approved Markdown knowledge documents**.
Every answer must be traceable to a `[Source: ...]` citation line, or the assistant refuses.

```
knowledge/approved/        authoritative YAML+Markdown records (human-reviewed)
knowledge/staging/         quarantine zone — never served by production pipeline
artifacts/                 derived data (graph.json, indexes) — safe to delete anytime
src/governance/            schema validator + staging ingest gate
src/admin/                 seed demo records, graph build, full rebuild
src/graph/                 Graphify config, edge classifier, NetworkX adapter
src/index/                 chunker, BM25 (SQLite FTS5), vector index (pluggable)
src/rag/                   RRF fusion, abstention gate, safety guard, entity linker,
                           graph evidence, context builder, query pipeline
src/llm/                   provider clients, constitutional prompt, citation validator
src/api/                   FastAPI server, admin CLI, embeddable chat widget
tests/                     unit / integration / retrieval / e2e / security suites
evaluation/                benchmark_100.json fixture + eval_runner.py
```

## 2. Day-to-Day Operations

### Validate knowledge corpus (run after ANY edit)
```powershell
& .venv\Scripts\python.exe -m src.governance.validator knowledge/approved
```

### Full deterministic rebuild (validate → graph → indexes → checksums)
```powershell
& .venv\Scripts\python.exe -m src.admin.rebuild_all
```
Fails hard on any invalid document; never publishes partial state.

### Serve the chatbot
```powershell
& .venv\Scripts\python.exe -m uvicorn src.api.server:app --port 8000
```
- UI demo page:  `http://localhost:8000/`
- Widget script: `/static/chat_widget.js` (single-file, embeddable)
- Health:        `GET /api/v1/health`
- Query:         `POST /api/v1/query` `{"message": "...", "history": [{...}]}`

### CLI inspection
```powershell
& .\.venv\Scripts\python.exe -m src.api.cli --query "What is the cutoff for CS?"
& .\.venv\Scripts\python.exe -m src.api.cli --interactive
```

## 3. Constitution Enforcement (what you must NOT do)

| Rule | Mechanism |
|---|---|
| No staging leakage | Production pipeline reads only `knowledge/approved/` |
| Temporal expiry | `review_before_date` < today ⇒ excluded; RPE `RETRIEVAL_EXPIRIED` logged |
| INFERRED edges never ground primary facts | Graph retriever filters them; audit sample: `python -m src.admin.audit_inferred 50` |
| Zero-fabrication | LLM replies are post-validated; missing/unknown citation ⇒ deterministic fallback with violation recorded |
| PES scope guard | Personal-contact / record / credential requests refused by `safety_guard.classify_request` |
| Budget eternity, prompt border, invocation ceiling | No optimizer bindings permitted (Constitution P7) |

## 4. LLM Provider Selection

| Provider | Usage | Notes |
|---|---|---|
| Retrieval-only (default) | no config | Deterministic extractive answers; still citation-locked. Use for zero-fabrication guarantee. |
| Ollama | `COLLEGE_CHATBOT_LLM_PROVIDER=ollama` (`OLLAMA_BASE_URL`, model `llama3.1:8b`) | Keep prompts=< 4k, max_tokens≈ 1022 tokens answer budget, ~1-2s/query. |
| Hosted (Anthropic) | `COLLEGE_CHATBOT_LLM_PROVIDER=hosted` (`ANTHROPIC_API_KEY`) | Fine for demos; never for scoped personal-record contexts anyway. |

Micro-budget per CPT02: hosted answers ≤ 1024 tokens; keep `<evidence>` ≤ 6000 chars
(both constants live in `src/rag/context_builder.py` and `src/llm/prompts.py`).

## 5. Answering Behavioral Governance

- Answer ALL corpus sources: the retrieval fallback returns top-2 chunk texts plus graph fact curated lines — never more than ~5 chunk citations.
- Refusal wording lists come from `src/rag/safety_guard.py`; they must cite nothing (no [Source: ...] lines).
- Note in code: pie removal of note ` For any non-retrievable question, mode=abstain`.

## 6. Incident Playbook

- **Validation fails at boot / rebuild:** fix or move invalid docs to `knowledge/staging/` — production serving uses the last valid in-memory snapshot only after successful boot.
- **Citation violations plague mode=llm:** AnswerValidator keeps the `violations` list in the AnswerResult trace; disable hosted mode (retrieval fallback kicks in automatically for that single response).
- **Expired fee docs:** update `review_before_date` + content in staging, re-approve into approved/, run rebuild.
- **Memory growth:** artifacts are derived; `Remove-Item artifacts -Recurse` then `rebuild_all` is always safe.

## 7. Test & Release Gates

```powershell
& .\.venv\Scripts\python.exe -m pytest tests -q            # full suite (123 tests)
& .\.venv\Scripts\python.exe evaluation\eval_runner.py      # empty-benchmark state report
```

Release checklist:
1. All merges to `master` require green `pytest`, validator PASS on approved/, and citation-drop audit on any hosted LLM smoke session.
2. Designated webmaster + college administrator approve DEPLOYMENT_DECISIONS.pdf sign-off.
3. Tag `v1.0.0-rc1` with `git tag -a` after checksum commit of `artifacts/rebuild_report.json`.
