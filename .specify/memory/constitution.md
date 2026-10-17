# College Information Chatbot — Project Constitution

## Core Principles

### I. Institutional Truth & Zero Fabrication (NON-NEGOTIABLE)
The chatbot exists solely to serve prospective students and parents with authoritative, approved institutional information.
- The chatbot MUST NEVER fabricate, assume, extrapolate, or hallucinate college facts, statistics, faculty members, accreditation, fees, scholarships, policies, or dates.
- If approved evidence is missing, conflicting, stale, or ambiguous, the chatbot MUST explicitly abstain ("I do not have verified college records on this topic. Please contact the admissions office.") rather than generate an unverified answer.
- Every claim presented to a user MUST cite an approved authoritative source document and section.

### II. Single Source of Truth & Knowledge Governance
Markdown documents stored under Git version control in `knowledge/approved/` constitute the sole authoritative source of truth.
- Direct website crawls, raw HTML, external feeds, and user prompts are UNAPPROVED discovery inputs.
- Unapproved discovery content MUST pass through a human-in-the-loop approval gate (Designated College Administrator) before being committed to the approved knowledge base.
- All derived indexes (vector embeddings, BM25 inverse indices, Graphify graph artifacts, community summaries) are ephemeral downstream projections. If an authoritative Markdown file is updated or retracted, downstream projections MUST be invalidated and rebuilt deterministically.

### III. Graph-Augmented RAG & Provenance Preservation
The system combines semantic vector search, BM25 lexical search, and graph-based traversal.
- Graph relationships MUST strictly preserve provenance: explicit relationships extracted from approved text (EXTRACTED) vs structural schema edges (STRUCTURAL) vs model-inferred edges (INFERRED).
- Inferred relationships MUST NOT be presented as official institutional facts unless corroborated by approved source evidence.
- Every chunk, entity, and edge MUST carry traceable metadata: source file, section, heading, version/commit hash, approver, and verification date.

### IV. Spec-Driven & Test-First Development
All system evolution follows the GitHub Spec Kit methodology.
- Development proceeds from Constitution → Feature Specification → Technical Plan → Task Breakdown → Test Implementation → Code Execution.
- No production feature code shall be written without an approved specification and failing automated tests (TDD).
- Planning artifacts and implementation gates must be approved by the human architect before execution begins.

### V. Local-First, Privacy-Preserving Architecture
The initial deployment target is local hardware or a college-controlled on-premises server.
- The chatbot MUST be capable of running fully offline without external cloud dependencies (using local embeddings and local LLMs) when privacy or air-gapped constraints dictate.
- The system MUST never log or persist personally identifiable information (PII) of prospective students or parents.
- Administrative operations (ingestion, approval, graph compilation) MUST be strictly separated from public query paths.

## Institutional Scope & Quality Boundaries
1. **In-Scope Domains:** College profile, academic departments, degree programs, curricula, faculty credentials/expertise, admissions criteria, fee schedules, scholarships, placement statistics, academic calendar, facilities (hostels, labs, library, transport), student services, clubs, and FAQs.
2. **Strictly Out-of-Scope:** Student personal academic records, individual exam marks, financial payment processing, confidential administrative deliberations, internal employee records, disciplinary logs.
3. **Quality Gate Thresholds:**
   - Retrieval Recall@5: >= 90%
   - Evidence-Supported Answer Correctness: >= 90%
   - Citation Integrity & Accuracy: >= 95%
   - Correct Abstention on Unanswerable Queries: >= 95%
   - Critical Unsupported Claims in Release Acceptance Set: 0%

## Governance & Amendment Rules
- This Constitution supersedes all implementation-level guidelines, prompts, and temporary configurations.
- Any amendment requires formal documentation, impact analysis across the Spec Kit artifacts, and approval from the designated project authority.
- Every Pull Request and release candidate must pass automated constitutional verification before merge.

**Version**: 1.0.0 | **Ratified**: 2026-10-17 | **Status**: Active Draft (Pending Final Review Gate)
