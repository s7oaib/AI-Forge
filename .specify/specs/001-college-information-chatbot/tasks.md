# Implementation Tasks: 001-college-information-chatbot
# Ordered Milestone Roadmap & Traceable Task Hierarchy

**Feature Identifier**: `001-college-information-chatbot`  
**Input**: [spec.md](file:///c:/Users/shoai/OneDrive/Desktop/AI%20FORGE/college-chatbot/.specify/specs/001-college-information-chatbot/spec.md), [plan.md](file:///c:/Users/shoai/OneDrive/Desktop/AI%20FORGE/college-chatbot/.specify/specs/001-college-information-chatbot/plan.md), [decision-register.md](file:///c:/Users/shoai/OneDrive/Desktop/AI%20FORGE/college-chatbot/.specify/specs/001-college-information-chatbot/decision-register.md)  
**Status**: Planning Mode Only (Implementation Blocked Pending Human Gate Approval)  
**Execution Convention**: `[T###] [P?] [Story/Phase] Task Description` ([P] = Parallel execution candidate)  

---

## Milestone Summary Matrix

| Milestone | Objective | Prerequisites | Estimated Effort | Target Deliverable |
|---|---|---|---|---|
| **M1** | Requirements, Constitution & Governance Foundation | None | 3 Days | Ratified Spec Kit baseline, ADRs, schema validator |
| **M2** | Website Audit & Approved Markdown Knowledge Base | M1 | 5 Days | Curated, validated Markdown repository in `knowledge/approved/` |
| **M3** | Graphify Pipeline & Entity-Relationship Modeling | M1, M2 | 4 Days | Automated Graphify extraction, graph schema, NetworkX adapter |
| **M4** | Hybrid RAG Indexing & Retrieval Engine | M1, M2 | 5 Days | BM25 + ChromaDB indexers, RRF fusion, Recall@5 benchmark |
| **M5** | Graph Integration & Evidence Fusion Engine | M3, M4 | 4 Days | Multi-hop graph walk, combined evidence scoring, graph citation |
| **M6** | Answer Generation, Citation Validator & Local UI | M4, M5 | 5 Days | Constitutional LLM prompt, citation validator, FastAPI + CLI |
| **M7** | Governance Automation, Security Audit, Eval & Release | M1–M6 | 5 Days | Automated 100-Q benchmark runner, penetration test, release tag |

---

## Detailed Milestone Task Breakdown

### Milestone 1: Requirements, Constitution & Governance Foundation
**Objective**: Establish project constitution, validate schemas, and setup testing frameworks before touching knowledge or code.
- **Dependencies**: None.
- **Related Spec Sections**: `spec.md § 1, 3, 5`, `constitution.md`.
- **Deliverables**: `.specify/` configuration, Pydantic metadata schema, automated frontmatter validator, CI pre-commit hooks.
- **Tasks**:
  - [x] **T001** `[M1]` Initialize Git repo hygiene, branch protection rules, and `.gitignore` for ephemeral artifacts (`artifacts/`, `.env`, `__pycache__`).
  - [x] **T002** `[P]` `[M1]` Implement Pydantic schema model for Markdown frontmatter (`src/core/schema.py`) enforcing ID, category, approval, and dates.
  - [x] **T003** `[P]` `[M1]` Implement automated YAML frontmatter parser and validator CLI (`src/governance/validator.py`).
  - [x] **T004** `[M1]` Create unit tests for schema validation (`tests/unit/test_schema.py`) covering valid, malformed, expired, and unapproved records.
  - [x] **T005** `[M1]` Formalize Requirements Decision Register (`decision-register.md`) and secure college administrator signoff on ADR-001 through ADR-008.
- **Checkpoint**: All schema validation unit tests pass. Constitution ratified.

---

### Milestone 2: Website Audit & Approved Markdown Knowledge Base
**Objective**: Audit the official college website and construct the authoritative, structured Markdown knowledge repository under `knowledge/approved/`.
- **Dependencies**: M1.
- **Related Spec Sections**: `spec.md § 4`, `plan.md § 4, 5`.
- **Deliverables**: Audited content map across 12 categories, initial batch of approved Markdown documents, ingestion linter.
- **Tasks**:
  - [x] **T006** `[M2]` Conduct site map crawl of official college website and produce URL inventory spreadsheet (`docs/website_audit_inventory.md`).
  - [x] **T007** `[P]` `[M2]` Create Markdown template files for all 12 categories in `knowledge/templates/`.
  - [x] **T008** `[M2]` Author initial core records for Profile, Admissions, Fees, and Departments using verified institutional data with synthetic fixtures for testing.
  - [x] **T009** `[P]` `[M2]` Author course curricula and faculty profile records (1 file per department/faculty) with explicit entity tags.
  - [x] **T010** `[M2]` Implement staging quarantine workflow (`src/governance/ingest_staging.py`) ensuring zero leaks from `knowledge/staging/` to production.
  - [x] **T011** `[M2]` Run automated schema validator across all authored documents; resolve all linter warnings.
- **Checkpoint**: $\ge 50$ approved Markdown records in `knowledge/approved/` passing 100% schema validation.

---

### Milestone 3: Graphify Feasibility & Graph Schema Modeling
**Objective**: Integrate Graphify extraction, define entity/edge schemas, and implement the high-speed in-memory NetworkX traversal adapter.
- **Dependencies**: M1, M2.
- **Related Spec Sections**: `spec.md § 3 (US3)`, `plan.md § 3`.
- **Deliverables**: Graph build script, Graphify extraction config, `artifacts/graph/graph.json`, NetworkX query adapter.
- **Tasks**:
  - [x] **T012** `[M3]` Configure Graphify extraction rules and entity patterns for academic terms (`src/graph/graphify_config.py`).
  - [x] **T013** `[M3]` Implement administrative graph compilation script (`src/admin/build_graph.py`) wrapping `graphify extract`.
  - [x] **T014** `[M3]` Implement graph audit parser (`src/graph/edge_classifier.py`) categorizing edges into `EXTRACTED`, `STRUCTURAL`, and `INFERRED`.
  - [x] **T015** `[P]` `[M3]` Implement in-memory NetworkX Graph Adapter (`src/graph/adapter.py`) supporting $k$-hop neighbor queries, shortest paths, and attribute lookup.
  - [x] **T016** `[M3]` Write graph integration tests (`tests/integration/test_graph_adapter.py`) validating multi-hop traversal latency ($\le 10\text{ms}$) and edge fidelity.
- **Checkpoint**: `graph.json` compiled and validated against college schema; multi-hop unit tests passing.

---

### Milestone 4: Hybrid RAG Indexing & Retrieval Engine
**Objective**: Build the semantic chunker, SQLite FTS5 lexical index, ChromaDB vector store, and Reciprocal Rank Fusion (RRF) retriever.
- **Dependencies**: M1, M2.
- **Related Spec Sections**: `spec.md § 5 (NFR-001, 004)`, `plan.md § 2`.
- **Deliverables**: Markdown chunker, BM25 indexer, Vector indexer, Hybrid RRF retriever, Retrieval benchmark runner.
- **Tasks**:
  - [x] **T017** `[M4]` Implement header-aware Markdown semantic chunker (`src/index/chunker.py`) with deterministic chunk ID hashing.
  - [x] **T018** `[P]` `[M4]` Implement SQLite FTS5 lexical BM25 indexer (`src/index/bm25_indexer.py`).
  - [x] **T019** `[P]` `[M4]` Implement ChromaDB vector store indexer (`src/index/vector_indexer.py`) with pluggable embedding providers.
  - [x] **T020** `[M4]` Implement Reciprocal Rank Fusion combiner (`src/rag/rrf.py`) fusing dense and lexical search candidates.
  - [x] **T021** `[M4]` Implement retrieval confidence filter and abstention gate (`src/rag/abstention_gate.py`).
  - [x] **T022** `[M4]` Write retrieval suite tests (`tests/retrieval/test_hybrid_retrieval.py`) proving Recall@5 $\ge 90\%$ on synthetic test corpus.
- **Checkpoint**: Hybrid retriever operational with $\le 150\text{ms}$ retrieval latency.

---

### Milestone 5: Graph Integration & Evidence Fusion
**Objective**: Connect the NetworkX graph traversal adapter into the hybrid RAG pipeline for multi-hop relational synthesis.
- **Dependencies**: M3, M4.
- **Related Spec Sections**: `spec.md § 3 (US3)`, `plan.md § 2 (Stage 8, 9)`.
- **Deliverables**: Unified evidence fusion engine, entity linker, relational context assembler.
- **Tasks**:
  - [x] **T023** `[M5]` Implement entity extraction and query alias matcher (`src/rag/entity_linker.py`).
  - [x] **T024** `[M5]` Implement Subgraph Evidence Extractor (`src/rag/graph_retriever.py`) extracting connected relational triples.
  - [x] **T025** `[M5]` Implement Unified Context Assembler (`src/rag/context_builder.py`) merging text chunks and graph triples into XML context tags.
  - [x] **T026** `[M5]` Implement temporal filtering logic (`src/rag/temporal_filter.py`) pruning expired records and legacy fee schedules.
  - [x] **T027** `[M5]` Write multi-hop end-to-end integration tests (`tests/integration/test_evidence_fusion.py`).
- **Checkpoint**: Combined text + graph evidence produced with unified provenance.

---

### Milestone 6: Answer Generation, Citation Validator & Local User Interface
**Objective**: Implement the constitutional zero-fabrication LLM client, automated citation post-validator, FastAPI server, and interactive CLI.
- **Dependencies**: M4, M5.
- **Related Spec Sections**: `spec.md § 3 (US1, US2), 5`, `plan.md § 7`.
- **Deliverables**: Pluggable LLM provider, citation regex validator, FastAPI REST server, CLI interactive runner, embeddable web widget.
- **Tasks**:
  - [x] **T028** `[M6]` Implement pluggable LLM provider client (`src/llm/client.py`) supporting Ollama (local) and approved hosted APIs.
  - [x] **T029** `[M6]` Build Constitutional Prompt generator (`src/llm/prompts.py`) strictly enforcing source citations and zero hallucination.
  - [x] **T030** `[M6]` Implement Answer & Citation Post-Validator (`src/llm/validator.py`) verifying that every inline citation matches an input chunk ID.
  - [x] **T031** `[P]` `[M6]` Implement FastAPI query endpoint (`POST /api/v1/query`) and health check (`GET /api/v1/health`) in `src/api/server.py`.
  - [x] **T032** `[P]` `[M6]` Implement interactive terminal CLI (`src/api/cli.py`) for administrator inspection and local user queries.
  - [x] **T033** `[P]` `[M6]` Build single-file embeddable Vanilla HTML/CSS/JS chat widget (`src/api/static/chat_widget.js`).
  - [x] **T034** `[M6]` Write end-to-end test suite (`tests/e2e/test_chat_e2e.py`) verifying student and parent persona journeys.
- **Checkpoint**: Full query loop responds with verified facts and exact citations in $\le 3.5\text{ seconds}$.

---

### Milestone 7: Governance Automation, Security Audit, Evaluation & Release
**Objective**: Automate index rebuilds, execute security & privacy penetration tests, run the 100-question evaluation benchmark, and tag release candidate.
- **Dependencies**: M1 through M6.
- **Related Spec Sections**: `spec.md § 5, 6`, `plan.md § 8`.
- **Deliverables**: 100-question evaluation dataset (`evaluation/benchmark_100.json`), automated eval report, security audit log, operator manual.
- **Tasks**:
  - [x] **T035** `[M7]` Build automated 100-question benchmark runner (`evaluation/eval_runner.py`) computing Recall@5, Answer Correctness, and Abstention Rate.
  - [x] **T036** `[M7]` Run security test suite (`tests/security/test_security.py`) covering prompt injection, PII leak prevention, and path traversal.
  - [x] **T037** `[M7]` Implement deterministic Index Invalidation & Rebuild CLI (`src/admin/rebuild_all.py`).
  - [x] **T038** `[M7]` Write comprehensive Administrator & Operator Guide (`docs/operator_manual.md`).
  - [ ] **T039** `[M7]` Conduct human review gate with designated college administrator and technical architect; obtain formal signoff.
  - [ ] **T040** `[M7]` Tag Release Candidate `v1.0.0-rc1` and generate deployment checksums.
- **Checkpoint**: 100% test pass rate; benchmark metrics meet or exceed constitutional thresholds; formal administrator approval granted.
