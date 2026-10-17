# Feature Specification: 001-college-information-chatbot
# College Information Chatbot (Graphify + GitHub Spec Kit + Hybrid RAG)

**Feature Identifier**: `001-college-information-chatbot`  
**Created**: 2026-10-17  
**Status**: Draft (Planning Mode Gate)  
**Target Audience**: Prospective Students, Parents, Secondary School Counselors  
**Approved Authority**: Designated College Administrator  
**Maintainer**: Central Knowledge Maintainer  

---

## 1. Executive Summary & Problem Statement

Prospective students and their parents face significant friction when navigating higher education websites. Essential information regarding program offerings, accreditation, eligibility criteria, fee structures, faculty qualifications, placement statistics, and hostel facilities is frequently fragmented across hundreds of disparate subpages, PDF handbooks, and outdated notices. 

Current LLM chat solutions deployed in academic institutions suffer from severe hallucination risks—often fabricating cutoff marks, scholarship eligibility, faculty rosters, or tuition fee amounts, which can cause reputational damage and legal liability.

This specification defines a reliable, source-grounded, privacy-preserving **College Information Chatbot** engineered with:
1. **GitHub Spec Kit** for rigorous specification-driven governance,
2. **Authoritative Markdown Knowledge Repository** (`knowledge/approved/`) under Git version control as the sole single source of truth,
3. **Graphify** for extracting entity-relationship graphs and structural knowledge networks,
4. **Hybrid RAG** (BM25 lexical search + dense vector retrieval + graph link traversal) with Reciprocal Rank Fusion (RRF),
5. **Zero-Fabrication Abstention Engine** enforcing citation grounding (`[Doc > Section > URL]`) and explicit refusal when verified institutional facts are unavailable.

---

## 2. User Personas & User Journeys

### Persona A: Prospective Student (Aarav, 18)
- **Profile**: Final-year high school student exploring undergraduate engineering and computer science programs.
- **Goals**: Discover degree options, understand eligibility cutoffs, check elective specializations (e.g., AI/ML, Cloud), review campus clubs/hackathons, and understand hostel facilities.
- **Pain Points**: Overwhelmed by massive multi-page academic handbooks; wants quick, concise, factual answers with direct links to application forms.
- **Primary Need**: Clear eligibility criteria, semester course outlines, and student life details.

### Persona B: Concerned Parent (Sunita, 48)
- **Profile**: Working parent evaluating college safety, total financial cost, accreditation, faculty quality, and career outcomes.
- **Goals**: Accurate annual fee schedules, scholarship criteria, faculty qualifications (PhD count, research domains), campus security, and verifiable 3-year placement statistics.
- **Pain Points**: Distrusts promotional brochures; requires verified numbers (average package, top recruiters, payment milestones).
- **Primary Need**: Official fee tables, refund policies, hostel security rules, and placement reports with clear dates and source citations.

### Persona C: College Knowledge Administrator (Dr. Raman, 52)
- **Profile**: Senior academic administrator responsible for institutional accuracy and compliance.
- **Goals**: Ensure the chatbot never disseminates obsolete syllabus versions, outdated fee figures, or unapproved admissions advice.
- **Pain Points**: Changes to fees or dates occur annually; needs a simple, auditable review workflow where changes must be signed off before the chatbot can speak them.
- **Primary Need**: Strict approval gates, provenance logging, deterministic rollback, and auditability.

---

## 3. Prioritized User Stories

### User Story 1 (P1): Direct Institutional Fact Retrieval with Strict Citation 🎯 MVP
**Description**: As a prospective student or parent, I want to ask direct factual questions (e.g., "What are the eligibility requirements for B.Tech Computer Science?") and receive an accurate, concise answer drawn strictly from approved college records, accompanied by an authoritative source citation and link.

- **Why this priority**: Forms the core utility of the chatbot. If direct factual retrieval with zero fabrication is not solved, the system cannot be deployed.
- **Independent Test**: Provide approved `admissions.md` and `departments.md`. Query the system with 10 standard factual questions. Verify 100% of answers match the approved text and provide valid `[Source: document.md # Section (URL)]` links.
- **Acceptance Scenarios**:
  1. **Given** approved records for B.Tech CS eligibility (minimum 75% in PCM), **When** user asks "What percentage is needed for CS?", **Then** the chatbot answers with 75% in PCM and cites the exact admissions document.
  2. **Given** no approved records for 2027 sports quota admissions, **When** user asks "What is the 2027 sports quota cutoff?", **Then** the chatbot explicitly abstains without guessing.

---

### User Story 2 (P1): Explicit Safe Abstention on Missing, Stale, or Ambiguous Facts 🎯 MVP
**Description**: As a user or administrator, when a question is asked about institutional topics that are not documented in the approved knowledge base, the chatbot must politely abstain, explain that verified records are not available, and provide the official admissions office contact details.

- **Why this priority**: Institutional integrity requires zero hallucination. Misinforming a parent about tuition fees or accreditation status is unacceptable.
- **Independent Test**: Query the chatbot with unapproved, hypothetical, or speculative queries (e.g., "What is the fee for Aerospace Engineering?" when no such program exists). Verify the chatbot responds with the standard abstention message and zero fabricated facts.
- **Acceptance Scenarios**:
  1. **Given** a query about an unoffered program, **When** the retrieval confidence score is below threshold ($\theta < 0.65$), **Then** the chatbot states: "I do not have verified college records regarding Aerospace Engineering. Please contact the Admissions Office at admissions@college.edu."
  2. **Given** a query asking for private faculty phone numbers, **When** processed, **Then** the chatbot refuses and points to the official department directory.

---

### User Story 3 (P2): Multi-Hop & Relational Graph Querying
**Description**: As a prospective student, I want to ask relational questions connecting departments, faculty, subjects, and prerequisites (e.g., "Who teaches Natural Language Processing, and what are their qualifications and research areas?") so that I can evaluate the academic depth of the department.

- **Why this priority**: Direct text search often retrieves disconnected snippets. Graph-augmented retrieval traverses entity edges (`Department -> Program -> Course -> Faculty -> Research Lab`) to compile comprehensive relational answers.
- **Independent Test**: Ingest approved department, course, and faculty Markdown records. Execute a 2-hop query. Verify the response synthesizes the course, instructor name, highest degree, and laboratory affiliation into a single answer with multi-source citations.
- **Acceptance Scenarios**:
  1. **Given** `faculty/dr_smith.md` (teaches CS402 NLP) and `courses/cs402.md`, **When** user asks "Who teaches NLP and what lab do they lead?", **Then** the chatbot identifies Dr. Smith, cites both files, and lists their lab affiliation.

---

### User Story 4 (P2): Temporal Filtering & Fee / Academic Calendar Grounding
**Description**: As a parent, I want to query fee schedules, deposit deadlines, and scholarship criteria for the current academic year (e.g., "What is the 2026-2027 tuition fee for Electronics Engineering, and when is the first installment due?") and ensure outdated fees from prior years are never returned.

- **Why this priority**: Financial decisions are time-sensitive. Serving a 2024 fee structure in 2026 can lead to legal disputes.
- **Independent Test**: Place both 2024–25 (archived/expired) and 2026–27 (active) fee tables into the repository. Query current tuition fees. Verify that the retrieval engine filters by `status: active` and `effective_year: 2026-2027`.
- **Acceptance Scenarios**:
  1. **Given** active and archived fee records, **When** user asks for current tuition, **Then** only active records are retrieved, and the response clearly states the academic year covered.

---

### User Story 5 (P3): Administrator Knowledge Governance, Ingestion & Rebuild
**Description**: As a College Knowledge Administrator, I want to inspect scraped website drafts in a staging folder, review changes, approve or reject them, and trigger an automated rebuild of the graph and vector indexes with complete git audit history.

- **Why this priority**: College websites change frequently (new circulars, faculty changes). A robust governance pipeline prevents unvetted web content from reaching prospective students.
- **Independent Test**: Submit a draft markdown file in `staging/`. Verify it is NOT retrievable. Move it to `approved/` with valid YAML frontmatter and run the index builder. Verify the new content is immediately searchable.
- **Acceptance Scenarios**:
  1. **Given** an unapproved file in `knowledge/staging/`, **When** any user query is run, **Then** zero chunks or graph nodes from the staging file are returned.
  2. **Given** an approved file retraction, **When** the file is moved to `knowledge/archived/` and reindexed, **Then** the chatbot abstains from answering queries based on that retracted document.

---

## 4. Supported Information Categories

The system must support answering inquiries across the following 12 core college domains:

| Category ID | Category Name | Typical Scope & Entities |
|---|---|---|
| **CAT-01** | College Profile & General Info | History, vision, accreditation (NAAC, NBA, ABET), campus location, affiliations, contact info. |
| **CAT-02** | Departments & Academic Units | Department lists, head of department (HOD), mission, affiliated labs, research centers. |
| **CAT-03** | Programs, Curricula & Courses | Degrees (B.Tech, M.Tech, Ph.D.), syllabi, course codes, credits, prerequisites, electives. |
| **CAT-04** | Faculty & Academic Staff | Faculty directory, designations, qualifications, research domains, office hours, public email. |
| **CAT-05** | Admissions & Eligibility | Minimum criteria, entrance exam cutoffs, application deadlines, seat intake, reservation policies. |
| **CAT-06** | Fees & Financial Aid | Tuition fees, hostel/mess fees, payment schedules, installment options, scholarships, waivers. |
| **CAT-07** | Placements, Recruiters & Internships | Placement statistics (median, average, highest CTC), major recruiters, placement cell contact. |
| **CAT-08** | Examinations & Regulations | Grading systems (CGPA/GPA), attendance rules, credit requirements, passing criteria, retake policies. |
| **CAT-09** | Academic Calendar & Key Dates | Semester commencement, mid-term/final exams, registration windows, vacation schedules. |
| **CAT-10** | Campus Facilities & Infrastructure | Library hours, digital resources, computer centers, student hostels, dining, sports, transport routes. |
| **CAT-11** | Student Services & Campus Life | Cultural/technical fests, student clubs, hackathons, grievance cell, anti-ragging committee, health center. |
| **CAT-12** | General FAQs | Common prospective queries, visitor directions, hostel rules, laptop recommendations. |

---

## 5. Non-Functional Requirements (NFR)

### Performance & Latency
- **NFR-001 (Retrieval Latency)**: Combined hybrid retrieval (BM25 + Vector + Graph search) must complete in $\le 500\text{ ms}$ on standard local server hardware (8 CPU cores, 16 GB RAM).
- **NFR-002 (End-to-End Latency)**: Total response time from query submission to complete answer delivery must be $\le 3.5\text{ seconds}$ when using local quantized LLM inference (e.g., Llama 3 8B Q4 via Ollama/vLLM) and $\le 2.0\text{ seconds}$ if using approved hosted API.
- **NFR-003 (Index Build Throughput)**: Ingestion, schema validation, chunking, Graphify execution, and index generation for 500 approved Markdown records must complete within 15 minutes.

### Accuracy & Source Grounding
- **NFR-004 (Retrieval Recall)**: Recall@5 must be $\ge 90\%$ on the 100-question baseline benchmark.
- **NFR-005 (Factual Grounding)**: Evidence-supported answer correctness must be $\ge 90\%$. Zero tolerance for hallucinated institutional metrics.
- **NFR-006 (Citation Precision)**: Every factual statement must have a traceable citation format `[Source: <Title> > <Heading> (<URL>)]` with $\ge 95\%$ accuracy.
- **NFR-007 (Abstention Precision)**: For unanswerable, out-of-scope, or unverified questions, the chatbot must achieve $\ge 95\%$ correct abstention.

### Security & Privacy
- **NFR-008 (Zero User PII Retention)**: The chatbot must never request, log, or persist user names, phone numbers, email addresses, or exam roll numbers. Session logs must be anonymized.
- **NFR-009 (Prompt Injection Resistance)**: The system must enforce prompt isolation where retrieved context cannot override system instructions or alter constitutional boundaries.
- **NFR-010 (Role Separation)**: Public query endpoints must have read-only access to compiled downstream artifacts. Administrative endpoints (ingestion, rebuild, approval) must require local authentication.

### Local Deployment & Portability
- **NFR-011 (Air-Gapped Viability)**: The entire query pipeline must be capable of executing fully offline on a local workstation without outbound internet connections.
- **NFR-012 (Reproducibility)**: Re-running the indexing pipeline against the same git commit of `knowledge/approved/` must produce bit-for-bit identical vector and graph indices.

---

## 6. Failure Modes & Fallback Behavior

| Trigger Condition | Detection Mechanism | System Action & Response |
|---|---|---|
| **Low Retrieval Confidence** | Max RRF score $< 0.035$ or Cosine Similarity $< 0.65$ | **Abstain**: "I could not find verified college documentation regarding your question. Please verify with the Admissions Office at [Admissions Email/Phone]." |
| **Conflicting Approved Data** | Chunks from different approved files assert conflicting numbers/dates | **Highlight & Defer**: "Our records indicate multiple dates for this event (Date A from Doc 1 and Date B from Doc 2). Please refer to the latest academic circular or contact the registrar." |
| **Stale / Expired Record** | Chunk metadata has `review_before < current_date` | **Flag & Warn**: Retrieve record but prefix response with: "[Note: This policy is currently scheduled for administrative review. Below is the last approved policy from Academic Year X]." |
| **Out-of-Scope Query** | Query intent classified as personal student records, fee payment, or internal grievance | **Polite Boundary Refusal**: "I am authorized only to provide public college information. For personal student records or fee payments, please log into the official Student Portal." |
| **LLM Runtime Unavailable** | Local LLM process crashes or API times out | **Graceful Degradation**: Fall back to direct extractive snippet presentation: "The AI generation service is temporarily unavailable. Here are the most relevant verified excerpts from college documents:" followed by raw retrieved snippets. |

---

## 7. Explicit Out-of-Scope Boundaries

The following capabilities are strictly forbidden and excluded from the system:
1. **Personal Student Data**: No access to individual student grades, transcripts, fee payment balances, attendance percentages, or disciplinary records.
2. **Financial Transactions**: No processing of tuition fee payments, application fee receipts, or banking details.
3. **Application Form Submission**: The chatbot will provide links and deadlines for applications but will NOT accept or submit applications.
4. **Autonomous Web Crawling to Production**: The system will NOT automatically scrape the web and publish to the live chatbot without designated administrator approval.
5. **Counseling Advice / Guaranteed Admissions**: The chatbot will NOT predict admissions chances or promise admission ("You have an 80% chance of getting in").

---

## 8. Requirements Traceability Matrix

| Requirement ID | Description | User Story | Verification Method |
|---|---|---|---|
| **FR-001** | Support 12 defined college knowledge categories | US1, US3, US4 | Category-level test queries |
| **FR-002** | Markdown frontmatter schema validation | US5 | Automated Pytest schema validator |
| **FR-003** | Human-in-the-loop approval gate (`knowledge/approved/`) | US5 | Directory boundary unit test |
| **FR-004** | Graphify graph extraction from approved Markdown | US3 | Graph build integration test |
| **FR-005** | Hybrid BM25 + Vector + Graph Link Walk Retrieval | US1, US3 | Retrieval recall benchmark |
| **FR-006** | Strict Citation Generation (`[Doc > Section > URL]`) | US1, US3 | Automated citation regex test |
| **FR-007** | Safe Abstention Engine for $\theta < \text{threshold}$ | US2 | 25 unanswerable test queries |
| **FR-008** | Temporal filtering by academic year and active status | US4 | Year-boundary integration test |
| **FR-009** | Graph provenance tagging (EXTRACTED vs INFERRED) | US3 | Graph node inspection test |
| **FR-010** | Local CLI and REST query interface | US1 | End-to-end API test |

---

**Approval**: Pending Human Architect Review Gate  
**Associated Spec Kit Documents**: `plan.md`, `decision-register.md`, `tasks.md`, `test-plan.md`
