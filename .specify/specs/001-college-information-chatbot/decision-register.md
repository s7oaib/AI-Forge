# Requirements & Architecture Decision Register (ADR)
# Feature: 001-college-information-chatbot

**Branch**: `master` | **Date**: 2026-10-17 | **Status**: Active Draft (Planning Review Gate)

This register tracks all critical technical, architectural, and governance decisions for the College Information Chatbot. Each entry is explicitly classified as **Confirmed**, **Proposed**, **Assumed**, or **Unresolved**.

---

## 1. Summary of Decision States

| Decision ID | Topic | Status | Approval Required | Decision Owner |
|---|---|---|---|---|
| **ADR-001** | Offline Execution vs Hosted AI APIs (LLM & Embeddings) | **Unresolved** | Yes (College Authority) | Lead Architect & College Admin |
| **ADR-002** | Vector Store Selection (ChromaDB vs LanceDB vs Qdrant) | **Proposed** | Yes (Technical Lead) | Backend / RAG Engineer |
| **ADR-003** | Lexical Search Engine (rank-bm25 vs SQLite FTS5) | **Proposed** | No (Internal Architecture)| RAG Engineer |
| **ADR-004** | Runtime Graph Engine (NetworkX Adapter vs Neo4j Server) | **Proposed** | Yes (Technical Lead) | Graph Engineer |
| **ADR-005** | Website Ingestion Strategy (Supervised Scraper vs Manual) | **Unresolved** | Yes (College Admin) | Knowledge Engineer & Admin |
| **ADR-006** | Student-Facing Frontend Scope (CLI + REST vs Next.js UI) | **Unresolved** | Yes (College Authority) | Product Owner |
| **ADR-007** | Concurrency & Scale Sizing (Local Server vs Cloud) | **Unresolved** | Yes (College IT Admin) | Infrastructure Lead |
| **ADR-008** | Ephemeral Index Invalidation & Build Trigger Protocol | **Confirmed** | Yes (Constitutional Gate)| Security & Governance Architect |

---

## 2. Detailed Decision Records

### ADR-001: Offline Execution vs Hosted AI APIs
- **Question**: Must the chatbot run 100% offline (air-gapped) on local college hardware, or is it permitted to call hosted commercial APIs (e.g., Anthropic Claude, OpenAI, Google Gemini, Voyage AI)?
- **Options**:
  - **Option A (Fully Offline)**: Ollama / vLLM running a quantized local open weights model (e.g., Llama 3.1 8B Q4 or Mistral 7B) + local HuggingFace embeddings (`BAAI/bge-small-en-v1.5`).
  - **Option B (Hosted Cloud APIs)**: Claude 3.5 Sonnet / Haiku or GPT-4o-mini via API + OpenAI `text-embedding-3-small`.
  - **Option C (Hybrid / Pluggable Adapter)**: Build an abstract `LLMProvider` and `EmbeddingProvider` interface in Python with a configuration flag (`LLM_BACKEND=local|hosted`), defaulting to local execution for privacy and local testing.
- **Recommended Option**: **Option C (Recommended - Hybrid / Pluggable)**.
- **Reasoning**: This prevents vendor lock-in, enables immediate zero-cost local development and offline validation, while allowing the college administration to switch to a fast hosted API in production if higher generation throughput or lower local hardware requirements are desired.
- **Risks & Trade-offs**:
  - Local LLM requires GPU hardware ($8\text{GB}+ \text{ VRAM}$) or fast 8-core CPU; slower token generation ($\sim 20 - 40\text{ tok/s}$).
  - Cloud APIs incur ongoing per-token financial costs and transmit prospective student query text over public networks.
- **Approval Required**: Designated College Administrator.
- **Current Status**: **Unresolved** (Defaulting to Option C with local Ollama fallback for planning).

---

### ADR-002: Vector Store Selection
- **Question**: Which vector database or library should be used to store and search chunk embeddings?
- **Options**:
  - **Option A (ChromaDB)**: Embedded in-process vector store using SQLite and duckdb/hnswlib.
  - **Option B (LanceDB)**: Serverless, disk-backed vector database optimized for multi-modal embeddings and fast columnar queries.
  - **Option C (Qdrant Local)**: Embedded or containerized vector search engine written in Rust.
- **Recommended Option**: **Option A (Recommended - ChromaDB in-process)**.
- **Reasoning**: Zero external daemon configuration required; runs completely in-process within Python; native support across the RAG ecosystem; lightweight storage in `artifacts/vector_index/`; easily committed or backed up.
- **Risks & Trade-offs**: Slightly slower than LanceDB on multi-million chunk datasets, but the college's approved knowledge base is expected to be under 10,000 chunks, where ChromaDB provides instant sub-10ms lookup.
- **Approval Required**: Technical Lead.
- **Current Status**: **Proposed**.

---

### ADR-003: Lexical / Exact Keyword Search Engine
- **Question**: What technology should power the BM25 lexical search component of the hybrid retriever?
- **Options**:
  - **Option A (`rank-bm25`)**: Pure Python in-memory implementation of the Okapi BM25 algorithm.
  - **Option B (SQLite FTS5)**: Embedded SQLite database utilizing Full-Text Search 5 virtual tables with BM25 ranking.
- **Recommended Option**: **Option B (Recommended - SQLite FTS5)**.
- **Reasoning**: SQLite is built into Python's standard library (`sqlite3`); FTS5 handles stemming, tokenization, phrase queries, and exact keyword matches without loading all documents into RAM; persistent file stored in `artifacts/bm25_index/fts5.db`.
- **Risks & Trade-offs**: Requires minimal SQL query construction, but eliminates Python memory bloat and enables incremental updates.
- **Approval Required**: Internal Architecture (No external approval needed).
- **Current Status**: **Proposed**.

---

### ADR-004: Runtime Graph Query Engine
- **Question**: Can Graphify meet runtime query performance and concurrency requirements directly, or is a separate runtime graph store/adapter required?
- **Options**:
  - **Option A (Graphify CLI Direct Runtime)**: Invoke `graphify query` as a subprocess for every student web query.
  - **Option B (In-Memory NetworkX Graphify Adapter)**: Use Graphify during build time to generate `artifacts/graph/graph.json`. At application startup, load `graph.json` into an in-memory `networkx.DiGraph` for $\le 5\text{ms}$ sub-graph traversals.
  - **Option C (Standalone Graph Database - Neo4j / FalkorDB)**: Run a dedicated Neo4j server, populated via `graphify export --format neo4j`.
- **Recommended Option**: **Option B (Recommended - In-Memory NetworkX Graphify Adapter)**.
- **Reasoning**: Graphify's CLI subprocess incurs $1.5 - 3.5\text{ seconds}$ startup latency per query, which violates NFR-001. A knowledge base of 500 college documents yields approximately 2,000–5,000 nodes and 10,000 edges, requiring only $15 - 30\text{ MB}$ of RAM in NetworkX. This gives sub-5ms traversal with zero external server dependencies. If the college expands to $> 100,000$ entities, Option C can be enabled via Graphify's native Cypher export.
- **Risks & Trade-offs**: In-memory graph requires re-loading if the process restarts (takes $\sim 200\text{ms}$ on boot).
- **Approval Required**: Technical Lead & Graph Engineer.
- **Current Status**: **Proposed**.

---

### ADR-005: Website Ingestion Pipeline Strategy
- **Question**: Should web discovery and scraping from the official college website be automated, semi-automated, or manual?
- **Options**:
  - **Option A (Fully Automated Scrape-to-Production)**: Web crawler runs periodically and pushes directly into the live chatbot index.
  - **Option B (Supervised Staging Pipeline)**: Automated web crawler extracts pages and converts them to draft Markdown in `knowledge/staging/`. A designated administrator inspects diffs, verifies accuracy, and promotes approved files to `knowledge/approved/`.
  - **Option C (100% Manual Authoring)**: The college communications office manually types or copies approved circulars directly into `knowledge/approved/`.
- **Recommended Option**: **Option B (Recommended - Supervised Staging Pipeline)**.
- **Reasoning**: Option A is constitutionally forbidden (violates Institutional Truth and human approval gate). Option C is too labor-intensive and causes stale data. Option B combines automated crawler efficiency with mandatory human-in-the-loop validation.
- **Risks & Trade-offs**: Requires an administrative review step, introducing slight lag before website changes reflect in the chatbot.
- **Approval Required**: Designated College Administrator.
- **Current Status**: **Unresolved** (Awaiting formal signoff from administrator).

---

### ADR-006: Student-Facing Frontend Scope
- **Question**: What user interface should be included in the initial release of the chatbot?
- **Options**:
  - **Option A (CLI + FastAPI REST Endpoints Only)**: Headless backend serving JSON responses; interactive command-line interface for testing.
  - **Option B (Single-Page Vanilla Web Chat Widget)**: Lightweight, accessible HTML/CSS/JavaScript floating widget that can be embedded into the college's existing CMS via a single `<script>` tag.
  - **Option C (Full Standalone Next.js Portal)**: Independent multi-page web application with user authentication, dashboard, and conversation history.
- **Recommended Option**: **Option B (Recommended - Vanilla Embeddable Web Widget + FastAPI REST)**.
- **Reasoning**: Option A cannot be used by real prospective students or non-technical parents. Option C adds unnecessary frontend complexity and authentication maintenance. Option B allows instant plug-and-play integration into the college's existing WordPress/Drupal/custom website without altering their existing infrastructure.
- **Risks & Trade-offs**: Frontend styling must be harmonized with college brand guidelines.
- **Approval Required**: Product Owner & College Communications Head.
- **Current Status**: **Unresolved** (Backend designed as API-first; frontend widget proposed).

---

### ADR-007: Concurrency & Scale Sizing
- **Question**: What is the target volume of concurrent prospective student inquiries during peak admissions season?
- **Options**:
  - **Option A (Low Volume / Campus Host)**: $5 - 10$ concurrent requests (typical departmental site).
  - **Option B (Medium Admissions Peak)**: $50 - 100$ concurrent requests (annual admissions results week).
  - **Option C (High-Throughput University Cloud)**: $1,000+$ concurrent requests.
- **Recommended Option**: **Option B (Medium Admissions Peak - 50-100 concurrent)**.
- **Reasoning**: Most college websites experience surges during entrance exam result releases and application deadline days. Designing with async FastAPI workers and in-memory read-only indexes easily satisfies 50–100 req/s on an 8-core machine.
- **Risks & Trade-offs**: If running local LLM inference, 50 concurrent requests will require queuing or batching via vLLM; a pure local 8-core CPU cannot sustain 50 parallel LLM generations without queuing.
- **Approval Required**: College IT Administrator.
- **Current Status**: **Unresolved** (Requires input on expected peak traffic).

---

### ADR-008: Ephemeral Index Invalidation & Build Trigger Protocol
- **Question**: When an authoritative Markdown file is modified, added, or deleted in `knowledge/approved/`, how should derived indexes be updated?
- **Options**:
  - **Option A (Full Deterministic Rebuild)**: Rebuild entire BM25, ChromaDB, and Graphify graph from scratch on every commit.
  - **Option B (Incremental Invalidation)**: Update only changed chunks in ChromaDB and BM25, and trigger Graphify rebuild for affected entity subgraphs.
- **Recommended Option**: **Option A (for $\le 1,000$ files) with planned migration to Option B**.
- **Reasoning**: For an initial knowledge base of 100–500 documents, a full deterministic rebuild takes under 5 minutes and completely eliminates edge-case sync bugs or orphaned graph nodes.
- **Risks & Trade-offs**: Slightly longer build time during updates, but 100% guarantee of consistency.
- **Approval Required**: Constitutional Ratification (Approved).
- **Current Status**: **Confirmed**.
