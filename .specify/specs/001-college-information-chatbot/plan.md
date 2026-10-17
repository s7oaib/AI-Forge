# Implementation Plan: 001-college-information-chatbot
# Technical Architecture & Pipeline Specification

**Branch**: `master` | **Created**: 2026-10-17 | **Spec**: [Feature Specification](file:///c:/Users/shoai/OneDrive/Desktop/AI%20FORGE/college-chatbot/.specify/specs/001-college-information-chatbot/spec.md)  
**Status**: Draft (Planning Mode Gate)  
**Target Runtime**: Python 3.11+, Local Workstation / On-Prem Server  

---

## 1. System Architecture & Logical Topology

The College Information Chatbot operates under a strict **bifurcated architecture** that permanently decouples the **Administrative Ingestion & Compilation Pipeline** from the **Runtime Query & Generation Pipeline**.

```
+---------------------------------------------------------------------------------------------------+
|                                ADMINISTRATIVE KNOWLEDGE PIPELINE                                  |
|                                                                                                   |
|  [Official Website / Circulars]                                                                  |
|               | (Manual / Supervised Scrape)                                                      |
|               v                                                                                   |
|     knowledge/staging/ (Draft Markdown)                                                           |
|               |                                                                                   |
|               v (Administrator Review & Cryptographic Signoff)                                    |
|     knowledge/approved/ (AUTHORITATIVE SOURCE OF TRUTH - Git Tracked)                             |
|               |                                                                                   |
|       +-------+----------------------------------+                                                |
|       |                                          |                                                |
|       v (Schema & AST Parsing)                   v (Graphify CLI Execution)                       |
|  [Chunker & Metadata Extractor]            [Graphify Extract & Cluster]                           |
|       |                                          |                                                |
|       +-------------------+                      v                                                |
|       |                   |               artifacts/graph/graph.json (NetworkX / Cypher)          |
|       v                   v                      |                                                |
| [Dense Embeddings]  [BM25 Inverted Index]        v                                                |
|  (Chroma / Qdrant)    (Rank-BM25 / SQLite FTS5)  |                                                |
|       |                   |                      |                                                |
+-------|-------------------|----------------------|------------------------------------------------+
        |                   |                      |
+-------v-------------------v----------------------v------------------------------------------------+
|                                    RUNTIME QUERY PIPELINE                                         |
|                                                                                                   |
|  [User Question (Student / Parent)]                                                              |
|       |                                                                                           |
|       v                                                                                           |
|  [Query Normalizer & Intent Classifier]                                                          |
|       |                                                                                           |
|       +-------------------+----------------------+                                                |
|       |                   |                      |                                                |
|       v (Dense Search)    v (Lexical Search)     v (Graph Subgraph Walk)                          |
|  [Vector Retriever]  [BM25 Retriever]      [Graphify Walk Adapter]                                |
|       |                   |                      |                                                |
|       +-------------------+----------------------+                                                |
|                           |                                                                       |
|                           v                                                                       |
|             [Reciprocal Rank Fusion (RRF)]                                                        |
|                           |                                                                       |
|                           v                                                                       |
|         [Evidence Filter & Abstention Gate]                                                       |
|              /                         \                                                          |
|     (Score >= 0.035)              (Score < 0.035)                                                 |
|            |                              |                                                       |
|            v                              v                                                       |
|  [Strict Citation LLM Prompt]     [Explicit Abstention Generator]                                |
|  (Local Llama 3 8B / Hosted)      ("I do not have verified college records...")                   |
|            |                              |                                                       |
|            v                              |                                                       |
|  [Answer & Citation Post-Validator]      |                                                       |
|            |                              |                                                       |
|            +--------------+---------------+                                                       |
|                           |                                                                       |
|                           v                                                                       |
|        [HTTP Response / CLI UI with Citations]                                                    |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. End-to-End 12-Stage Pipeline

1. **Stage 1: Approved Source Discovery & Staging**
   - Web discovery drafts or administrative circulars are drafted into `knowledge/staging/`.
   - Content in `staging/` is strictly quarantined from all search and graph indexes.

2. **Stage 2: Markdown Parsing & Schema Validation**
   - The Designated Administrator reviews and moves verified documents to `knowledge/approved/`.
   - A deterministic parser parses YAML frontmatter and validates fields (`id`, `title`, `category`, `source_url`, `status`, `approved_by`, `last_verified`, `effective_year`).
   - If schema validation fails, the build halts immediately.

3. **Stage 3: Semantic Chunking & Entity Identification**
   - Documents are partitioned by Markdown semantic headers (`## `, `### `) rather than arbitrary token boundaries, ensuring paragraphs, tables, and lists stay intact.
   - Each chunk receives a deterministic unique chunk ID: `<doc_id>#<header-slug>`.
   - Each chunk retains inherited document metadata plus local section titles.

4. **Stage 4: Keyword & Vector Indexing**
   - **BM25 Inverted Index**: Built using `rank-bm25` (or SQLite FTS5) over chunk plain text for exact matching of course codes (`CS402`), faculty names (`Dr. Raman`), and specific acronyms.
   - **Dense Vector Index**: Chunks are embedded using a local embedding model (e.g., `BAAI/bge-small-en-v1.5` or `all-MiniLM-L6-v2`) and indexed into an embedded vector store (`chromadb` or `lancedb`).

5. **Stage 5: Graph Generation & Relationship Validation (Graphify Build Phase)**
   - `graphify extract` is executed over `knowledge/approved/` using an approved local/hosted extraction model.
   - Nodes and edges are generated and written to `artifacts/graph/graph.json`.
   - Edges are audited and classified:
     - `EXTRACTED`: Explicitly stated in approved text (e.g., "Dr. Smith teaches CS402").
     - `STRUCTURAL`: Derived from frontmatter links (e.g., `department: CSE` $\rightarrow$ `CSE Department`).
     - `INFERRED`: Derived by LLM clustering.
   - Inferred edges are tagged with a lower confidence weight ($0.5$) and cannot be cited as primary facts.

6. **Stage 6: Query Normalization & Intent Detection**
   - Incoming user questions are normalized (spelling correction for acronyms, whitespace trimming).
   - An intent classifier determines whether the question is:
     - Direct Factual (e.g., "What is the fee for B.Tech?"),
     - Relational / Multi-hop (e.g., "Which professor teaches Cloud and what are their qualifications?"),
     - Out-of-Scope (e.g., "What is my semester GPA?"),
     - Adversarial / Injection (e.g., "Ignore previous instructions").

7. **Stage 7: Hybrid RAG Retrieval (Dense + Lexical)**
   - Query is submitted concurrently to the Vector Index ($k=10$) and the BM25 Index ($k=10$).
   - Returns candidate chunks with similarity scores.

8. **Stage 8: Graph Retrieval & Subgraph Walk**
   - Extracted entities in the query (matched via alias dictionary or NER) seed a subgraph traversal in `artifacts/graph/graph.json` via NetworkX.
   - Traverses 1 to 2 hops along approved edge types (`OFFERS_PROGRAM`, `INCLUDES_COURSE`, `TAUGHT_BY`, `LOCATED_AT`, `ELIGIBILITY_FOR`).
   - Connected entity attributes and relationship summaries are converted into factual evidence triples.

9. **Stage 9: Evidence Fusion & Filtering (Reciprocal Rank Fusion)**
   - Scores from BM25, Vector, and Graph paths are fused using Reciprocal Rank Fusion:
     $$RRF(d) = \sum_{m \in M} \frac{w_m}{60 + r_m(d)}$$
   - Chunks with composite $RRF < \text{threshold}$ are pruned.
   - If top-ranked evidence score is below the abstention threshold ($\theta = 0.035$), the pipeline branches immediately to Stage 12 (Abstention).

10. **Stage 10: Context Assembly & Prompt Construction**
    - High-ranking chunks are formatted with strict source tags:
      ```xml
      <evidence id="1" doc="admissions.md" section="B.Tech Eligibility" url="https://college.edu/admissions">
      Minimum 75% aggregate in 10+2 with Physics, Chemistry, and Mathematics.
      </evidence>
      ```
    - The system prompt forbids external world knowledge and demands inline citations `[1]`.

11. **Stage 11: Answer Generation & Citation Validation**
    - The LLM generates the response adhering to the constitutional prompt.
    - An automated post-validator parses the generated answer:
      - Validates that every claim cited refers to an existing `<evidence id="...">`.
      - Checks that no forbidden phrases or uncited numerical statistics are present.
      - If citation checks fail, response is rejected or re-prompted.

12. **Stage 12: Logging, Feedback & Safe Output Formatting**
    - Response is delivered to the user with clickable source references.
    - Query and response are logged with anonymized session IDs (zero PII) for administrator audit and offline regression evaluation.

---

## 3. Graphify Feasibility Analysis & Runtime Strategy

### What Graphify Is
Based on verification of the official Graphify codebase (v0.9.55):
- Graphify is a specialized Python-based **AST + Semantic extraction and graph clustering tool**.
- It analyzes code repositories and Markdown/text corpora, extracting entities, calls, types, concepts, and relationships.
- It applies graph community detection (Leiden / Louvain / graspologic) to create multi-scale hierarchical summaries.
- It exports graphs to JSON (`graph.json`), interactive visualizers (`graph.html`), Obsidian vaults, FalkorDB, and Neo4j Cypher scripts.
- It provides an interactive agent query tool (`graphify query`) using BM25 seed selection + BFS/DFS walk + LLM summarization.

### Technical Limitations of Graphify for Pure Runtime RAG
1. **Subprocess Overhead**: Invoking `graphify query` as an external CLI subprocess per user query incurs $\sim 1.5 - 3.5\text{ seconds}$ of process startup and model loading overhead.
2. **Concurrency Constraints**: `graphify query` is designed as a single-user CLI investigation tool, lacking thread pools, async web handlers, or connection pooling for multi-user concurrent traffic.
3. **No Native Vector Search**: Graphify relies on lexical BM25 matching for initial entity seed selection; it does not perform dense semantic vector search out of the box.

### Proposed Architectural Solution: Two-Phase Graphify Strategy
To capture the full power of Graphify while maintaining sub-second query latency and enterprise reliability, we adopt the following pattern:

- **Build Time (Compilation)**:
  Use `graphify extract` over `knowledge/approved/` during the administrative indexing phase. This generates the authoritative `artifacts/graph/graph.json` and hierarchical community summaries.
- **Runtime (Query Serving)**:
  Implement an in-memory **Graphify Walk Adapter** in Python using `networkx`. At application boot, the server loads `graph.json` into memory ($< 25\text{ MB}$ for thousands of nodes). When a query arrives, entity nodes are resolved via an in-memory alias dictionary, followed by a $k$-hop directed walk ($\le 5\text{ ms}$).
- **Optional Enterprise Scale**:
  If graph volume exceeds in-memory limits ($> 100,000$ entities), the pipeline provides a zero-code exporter to Neo4j or FalkorDB using Graphify's built-in `graphify export --format neo4j` command.

---

## 4. Authoritative Knowledge Repository Structure

The knowledge base in the repository will be structured as follows:

```text
college-chatbot/
├── .specify/                         # GitHub Spec Kit configuration & memory
│   ├── memory/constitution.md        # Core institutional rules
│   └── specs/001-college-information-chatbot/
│       ├── spec.md                   # Feature specification
│       ├── plan.md                   # This architecture plan
│       ├── decision-register.md      # Requirements Decision Register (ADRs)
│       ├── tasks.md                  # Milestone & task hierarchy
│       └── test-plan.md              # Test plan & evaluation benchmark
├── knowledge/                        # Knowledge Base Root
│   ├── approved/                     # AUTHORITATIVE SOURCE OF TRUTH (Git Tracked)
│   │   ├── profile/                  # CAT-01: College overview, accreditation, history
│   │   ├── departments/              # CAT-02: Department records (1 file per dept)
│   │   ├── programs/                 # CAT-03: Degree programs (B.Tech, M.Tech, etc.)
│   │   ├── courses/                  # CAT-03: Individual course syllabi & electives
│   │   ├── faculty/                  # CAT-04: Faculty profiles (1 file per faculty)
│   │   ├── admissions/               # CAT-05: Criteria, cutoffs, intake capacity
│   │   ├── fees_scholarships/        # CAT-06: Fee schedules, installment rules, waivers
│   │   ├── placements/               # CAT-07: Placement statistics, recruiters, reports
│   │   ├── academics/                # CAT-08, 09: Exam regulations, grading, calendar
│   │   ├── facilities/               # CAT-10: Hostels, labs, library, transport
│   │   ├── campus_life/              # CAT-11: Clubs, student chapters, fests, cells
│   │   └── faqs/                     # CAT-12: Curated general FAQs
│   ├── staging/                      # UNAPPROVED Discovery / Scraped Drafts (Ignored by runtime)
│   └── archived/                     # Retired / Superceded historical records
├── artifacts/                        # DERIVED ARTIFACTS (Reproducible from approved/)
│   ├── graph/                        # Graphify outputs (graph.json, graph.html, communities)
│   ├── vector_index/                 # Chroma / LanceDB persistent files
│   └── bm25_index/                   # Inverted lexical index
├── evaluation/                       # Evaluation & Benchmark Datasets
│   ├── benchmark_100.json            # 100 curated test questions & ground truth
│   └── eval_runner.py                # Automated precision/recall/citation evaluator
├── src/                              # Python Application Source Code
│   ├── admin/                        # Ingestion, validation, and index build tools
│   ├── core/                         # Configuration, logging, models, schemas
│   ├── governance/                   # Approval verification, git provenance checks
│   ├── graph/                        # Graphify loader & NetworkX traversal adapter
│   ├── index/                        # BM25 & Vector index managers
│   ├── rag/                          # Retrieval, RRF fusion, context assembly
│   ├── llm/                          # Local/hosted LLM providers & citation prompts
│   └── api/                          # FastAPI / Flask REST query endpoints & CLI
└── tests/                            # Automated Pytest Suite
    ├── unit/                         # Schema, chunking, citation regex tests
    ├── integration/                  # Ingestion, indexing, graph walk tests
    ├── retrieval/                    # Recall@5, BM25, hybrid ranking tests
    ├── governance/                   # Approval gates & quarantine tests
    └── security/                     # Injection, secret leak, privacy tests
```

---

## 5. Authoritative Markdown Schema & Frontmatter Specification

Every file in `knowledge/approved/` must contain standardized YAML frontmatter conforming to this schema:

```yaml
---
id: "FAC-CSE-042"                      # Unique permanent entity identifier
title: "Dr. Arvind Raman - Professor & Head, Computer Science"
category: "faculty"                    # One of the 12 defined categories
slug: "faculty-arvind-raman"
department_id: "DEPT-CSE"
official_url: "https://college.edu/faculty/arvind-raman"
source_retrieval_date: "2026-10-15"
approval_status: "approved"            # approved | pending | rejected | archived
approved_by: "administrator@college.edu"
approval_date: "2026-10-16"
last_verified_date: "2026-10-16"
effective_academic_year: "2026-2027"
review_before_date: "2027-06-30"       # Expiry / review date
version: "1.2.0"
entities:
  - id: "FAC-CSE-042"
    type: "Person"
    name: "Dr. Arvind Raman"
  - id: "DEPT-CSE"
    type: "Department"
    name: "Computer Science and Engineering"
relationships:
  - source: "FAC-CSE-042"
    relation: "HEAD_OF"
    target: "DEPT-CSE"
  - source: "FAC-CSE-042"
    relation: "TEACHES"
    target: "COURSE-CS402"
keywords:
  - "Arvind Raman"
  - "HOD CSE"
  - "Natural Language Processing"
  - "Machine Learning"
---

# Dr. Arvind Raman

## Academic Profile & Qualifications
- **Designation**: Professor & Head of Department
- **Highest Degree**: Ph.D. in Computer Science (IIT Bombay, 2014)
- **Specialization**: Natural Language Processing, Information Retrieval, Knowledge Graphs

## Teaching & Courses Taught
- **CS402**: Natural Language Processing (Undergraduate Elective)
- **CS701**: Advanced Artificial Intelligence (Postgraduate Core)

## Research & Laboratories Led
- Director, Language Technologies Research Center (LTRC)
...
```

---

## 6. Technology Stack & Component Selection

| Component | Selected / Proposed Tool | Rationale | Unresolved Status |
|---|---|---|---|
| **Backend Language** | Python 3.11+ | Native compatibility with Graphify, NetworkX, LangChain/LlamaIndex, Pytest | **Confirmed** |
| **Specification Tool** | GitHub Spec Kit (`specify-cli 1.2.2.dev0`) | Constitutional governance, spec-driven development | **Confirmed** |
| **Knowledge Store** | Markdown + YAML Frontmatter (Git) | Auditable, human-readable, transparent, zero lock-in | **Confirmed** |
| **Graph Generation** | Graphify (`v0.9.55`) | AST + Semantic extraction, community clustering | **Confirmed** |
| **Runtime Graph Store**| NetworkX in-memory adapter (from `graph.json`) | Sub-millisecond queries, zero external DB overhead | **Proposed (ADR-004)** |
| **Lexical Search** | `rank-bm25` / SQLite FTS5 | Exact match for course codes, dates, names | **Proposed (ADR-003)** |
| **Vector Store** | ChromaDB / LanceDB (Embedded) | Embedded local execution, no separate daemon needed | **Proposed (ADR-002)** |
| **Embedding Model** | `BAAI/bge-small-en-v1.5` (Local) / OpenAI text-embedding-3-small | High MTEB score, lightweight, fast CPU inference | **Unresolved (ADR-001)**|
| **LLM Inference** | Ollama (Llama 3.1 8B Q4) or Approved Hosted API | Local privacy vs hosted generation speed | **Unresolved (ADR-001)**|
| **API Framework** | FastAPI | High throughput, async, automatic OpenAPI docs | **Proposed** |

---

## 7. Zero-Fabrication Prompt Specification

```text
[SYSTEM CONSTITUTION]
You are the official College Information Assistant for prospective students and parents.
Your mission is to provide 100% accurate, factual institutional information strictly based on the provided VERIFIED COLLEGE EVIDENCE below.

CRITICAL RULES:
1. NEVER use outside world knowledge or extrapolate beyond the provided text.
2. If the provided evidence does not contain the answer, or if evidence is ambiguous or missing, you MUST reply:
   "I do not have verified college records on this topic. Please contact the Admissions Office at [Admissions Email/Phone] for official assistance."
3. EVERY factual claim, date, fee number, or qualification you state MUST include an inline citation in the format [DocTitle > SectionName].
4. Never promise admission, predict cutoff percentiles, or offer personal counseling opinions.

[VERIFIED COLLEGE EVIDENCE]
{context_chunks}

[USER QUESTION]
{user_query}

[ASSISTANT RESPONSE]
```

---

## 8. Definition of Done for Technical Plan

- [x] Architecture topology and dataflow diagrams documented.
- [x] 12-stage pipeline from staging to citation generation specified.
- [x] Graphify feasibility, runtime limitations, and two-phase adapter strategy detailed.
- [x] Comprehensive Markdown frontmatter schema defined.
- [x] Repository directory layout defined with clear separation of authoritative vs derived data.
- [x] Zero-fabrication prompt and citation enforcement protocol documented.
