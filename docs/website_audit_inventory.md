# Official College Website Audit & Content Inventory

**Institution**: Greenfield Institute of Technology (Demo / Reference College)  
**Website Baseline**: `https://greenfield.edu`  
**Audit Date**: 2026-10-17  
**Auditor**: Central Knowledge Engineering Team  
**Designated Administrator**: `provost-desk@greenfield.edu`  
**Status**: Initial Baseline Audit Complete (12 Institutional Categories)

---

## 1. Executive Summary & Crawl Scope

A systematic structural crawl of the official college web presence (`https://greenfield.edu`) was conducted to establish the authoritative discovery baseline. In accordance with the project constitution (**Principle 1: Authoritative Source of Truth** and **Principle 3: Strict Governance Gate**), website content is treated as discovery material only and must be reviewed, transcribed into structured Markdown with Pydantic-compliant metadata, and formally approved before entering the active knowledge base.

### Summary Metrics
- **Total URLs Cataloged**: 54 endpoints across 12 institutional categories.
- **Content Types**: Static policy pages, department curricula, faculty registries, fee schedules, examination circulars, campus facility guides.
- **Dynamic / Prohibited Scope**: Live ERP student portals, fee payment gateways, confidential student grade portals, and internal personnel systems are strictly excluded from ingestion.

---

## 2. Institutional Category Inventory Map

| URL Path | Canonical Page Title | Category | Target Document ID | Target Markdown Path | Audit Status | Approval Authority |
|---|---|---|---|---|---|---|
| `/about/overview` | About Greenfield Institute of Technology | `profile` | `DOC-PROF-001` | `knowledge/approved/profile/overview.md` | Audited | College Registrar |
| `/about/leadership` | Governance, Vision, and Leadership | `profile` | `DOC-PROF-002` | `knowledge/approved/profile/leadership.md` | Audited | Office of the President |
| `/about/accreditation` | Accreditations, Affiliations & NIRF Ranking | `profile` | `DOC-PROF-003` | `knowledge/approved/profile/accreditations.md` | Audited | Quality Assurance Cell |
| `/academics/departments/cse` | Dept of Computer Science & Engineering | `departments` | `DOC-DEPT-001` | `knowledge/approved/departments/cse.md` | Audited | Head, CSE |
| `/academics/departments/ece` | Dept of Electronics & Communication | `departments` | `DOC-DEPT-002` | `knowledge/approved/departments/ece.md` | Audited | Head, ECE |
| `/academics/departments/me` | Dept of Mechanical Engineering | `departments` | `DOC-DEPT-003` | `knowledge/approved/departments/me.md` | Audited | Head, ME |
| `/academics/departments/civil` | Dept of Civil Engineering | `departments` | `DOC-DEPT-004` | `knowledge/approved/departments/civil.md` | Audited | Head, Civil |
| `/academics/programs/btech-cse` | Bachelor of Technology in CSE | `programs` | `DOC-PROG-001` | `knowledge/approved/programs/btech_cse.md` | Audited | Dean of Academics |
| `/academics/programs/btech-ai` | B.Tech in Artificial Intelligence & Data Science | `programs` | `DOC-PROG-002` | `knowledge/approved/programs/btech_ai_ds.md` | Audited | Dean of Academics |
| `/academics/programs/btech-ece` | Bachelor of Technology in ECE | `programs` | `DOC-PROG-003` | `knowledge/approved/programs/btech_ece.md` | Audited | Dean of Academics |
| `/academics/programs/mtech-cse` | Master of Technology in Computer Science | `programs` | `DOC-PROG-004` | `knowledge/approved/programs/mtech_cse.md` | Audited | Dean of Academics |
| `/academics/courses/cs101` | CS101: Introduction to Computing | `courses` | `DOC-CRS-001` | `knowledge/approved/courses/cs101.md` | Audited | Board of Studies |
| `/academics/courses/cs201` | CS201: Data Structures and Algorithms | `courses` | `DOC-CRS-002` | `knowledge/approved/courses/cs201.md` | Audited | Board of Studies |
| `/academics/courses/cs301` | CS301: Database Management Systems | `courses` | `DOC-CRS-003` | `knowledge/approved/courses/cs301.md` | Audited | Board of Studies |
| `/academics/courses/ai201` | AI201: Foundations of Artificial Intelligence | `courses` | `DOC-CRS-004` | `knowledge/approved/courses/ai201.md` | Audited | Board of Studies |
| `/academics/courses/ec101` | EC101: Network Analysis and Signals | `courses` | `DOC-CRS-005` | `knowledge/approved/courses/ec101.md` | Audited | Board of Studies |
| `/academics/faculty/dr-elena-rodriguez` | Faculty Profile: Dr. Elena Rodriguez (HOD CSE) | `faculty` | `DOC-FAC-001` | `knowledge/approved/faculty/dr_elena_rodriguez.md` | Audited | Dean Faculty Affairs |
| `/academics/faculty/dr-marcus-vance` | Faculty Profile: Dr. Marcus Vance (Prof CSE) | `faculty` | `DOC-FAC-002` | `knowledge/approved/faculty/dr_marcus_vance.md` | Audited | Dean Faculty Affairs |
| `/academics/faculty/dr-sarah-chen` | Faculty Profile: Dr. Sarah Chen (Assoc Prof AI) | `faculty` | `DOC-FAC-003` | `knowledge/approved/faculty/dr_sarah_chen.md` | Audited | Dean Faculty Affairs |
| `/academics/faculty/dr-rajesh-sharma` | Faculty Profile: Dr. Rajesh Sharma (HOD ECE) | `faculty` | `DOC-FAC-004` | `knowledge/approved/faculty/dr_rajesh_sharma.md` | Audited | Dean Faculty Affairs |
| `/admissions/overview` | Admissions Overview & Timeline (2026-2027) | `admissions` | `DOC-ADM-001` | `knowledge/approved/admissions/overview.md` | Audited | Director Admissions |
| `/admissions/undergraduate-eligibility` | UG Eligibility Criteria & Quotas | `admissions` | `DOC-ADM-002` | `knowledge/approved/admissions/ug_eligibility.md` | Audited | Director Admissions |
| `/admissions/postgraduate-eligibility` | PG Eligibility & GATE Requirements | `admissions` | `DOC-ADM-003` | `knowledge/approved/admissions/pg_eligibility.md` | Audited | Director Admissions |
| `/admissions/international` | International & NRI Student Admissions | `admissions` | `DOC-ADM-004` | `knowledge/approved/admissions/international.md` | Audited | International Office |
| `/admissions/counseling-procedure` | Seat Allocation & Counseling Process | `admissions` | `DOC-ADM-005` | `knowledge/approved/admissions/counseling.md` | Audited | Director Admissions |
| `/fees/tuition-ug` | UG Tuition & Composite Fee Schedule | `fees_scholarships` | `DOC-FEE-001` | `knowledge/approved/fees_scholarships/ug_tuition.md` | Audited | Finance Officer |
| `/fees/tuition-pg` | PG Fee Structure & Laboratory Charges | `fees_scholarships` | `DOC-FEE-002` | `knowledge/approved/fees_scholarships/pg_tuition.md` | Audited | Finance Officer |
| `/fees/hostel-transport` | Hostel & Transportation Fee Schedule | `fees_scholarships` | `DOC-FEE-003` | `knowledge/approved/fees_scholarships/hostel_fees.md` | Audited | Chief Warden / Transport |
| `/fees/scholarships-merit` | Merit & Need-Based Scholarships | `fees_scholarships` | `DOC-FEE-004` | `knowledge/approved/fees_scholarships/scholarships.md` | Audited | Financial Aid Committee |
| `/fees/refund-policy` | Fee Refund & Withdrawal Rules | `fees_scholarships` | `DOC-FEE-005` | `knowledge/approved/fees_scholarships/refund_policy.md` | Audited | Finance Officer |
| `/placements/overview` | Career Development Cell & Placement Stats | `placements` | `DOC-PLC-001` | `knowledge/approved/placements/overview.md` | Audited | Head, CDC Placements |
| `/placements/top-recruiters` | Major Recruiters & Sector Distribution | `placements` | `DOC-PLC-002` | `knowledge/approved/placements/recruiters.md` | Audited | Head, CDC Placements |
| `/placements/internships` | Summer Internship Program & Policies | `placements` | `DOC-PLC-003` | `knowledge/approved/placements/internships.md` | Audited | Head, CDC Placements |
| `/academics/regulations` | Academic Regulations & Grading System | `academics` | `DOC-ACAD-001` | `knowledge/approved/academics/regulations.md` | Audited | Controller of Exams |
| `/academics/attendance-policy` | Mandatory Attendance & Leave Policy | `academics` | `DOC-ACAD-002` | `knowledge/approved/academics/attendance.md` | Audited | Dean of Academics |
| `/academics/calendar-2026-2027` | Official Academic Calendar 2026-2027 | `academics` | `DOC-ACAD-003` | `knowledge/approved/academics/calendar.md` | Audited | Registrar |
| `/campus/central-library` | Central Library Resources & Borrowing Rules | `facilities` | `DOC-FACIL-001` | `knowledge/approved/facilities/library.md` | Audited | Chief Librarian |
| `/campus/computing-labs` | Computing Infrastructure & High-Performance Lab | `facilities` | `DOC-FACIL-002` | `knowledge/approved/facilities/computing_labs.md` | Audited | Systems Administrator |
| `/campus/hostels-dining` | Student Residences & Dining Facilities | `facilities` | `DOC-FACIL-003` | `knowledge/approved/facilities/hostels.md` | Audited | Chief Warden |
| `/campus/health-sports` | Health Center, Gymnasium & Sports Facilities | `facilities` | `DOC-FACIL-004` | `knowledge/approved/facilities/sports_health.md` | Audited | Medical Officer / Sports Dir |
| `/campus/transport` | Campus Shuttle & Commuter Bus Routes | `facilities` | `DOC-FACIL-005` | `knowledge/approved/facilities/transport.md` | Audited | Transport Manager |
| `/student-life/clubs` | Student Technical & Cultural Clubs | `campus_life` | `DOC-LIFE-001` | `knowledge/approved/campus_life/clubs.md` | Audited | Dean Student Welfare |
| `/student-life/annual-fests` | Annual Tech Fest (InnovateX) & Cultural Fest (Aura) | `campus_life` | `DOC-LIFE-002` | `knowledge/approved/campus_life/fests.md` | Audited | Dean Student Welfare |
| `/student-life/counseling-wellness` | Student Counseling, Mentorship & Grievance | `campus_life` | `DOC-LIFE-003` | `knowledge/approved/campus_life/mentorship.md` | Audited | Chief Counselor |
| `/faqs/admissions-general` | Admissions & Eligibility FAQs | `faqs` | `DOC-FAQ-001` | `knowledge/approved/faqs/admissions_faq.md` | Audited | Admissions Cell |
| `/faqs/fees-scholarships` | Fee Payment & Scholarship FAQs | `faqs` | `DOC-FAQ-002` | `knowledge/approved/faqs/fees_faq.md` | Audited | Accounts Office |
| `/faqs/hostel-life` | Hostel Allotment & Campus Living FAQs | `faqs` | `DOC-FAQ-003` | `knowledge/approved/faqs/hostel_faq.md` | Audited | Hostel Office |
| `/faqs/placements-careers` | Placement Preparation & Eligibility FAQs | `faqs` | `DOC-FAQ-004` | `knowledge/approved/faqs/placements_faq.md` | Audited | Placement Officer |

---

## 3. Discrepancy & Gap Analysis
1. **Academic Year Scope**: The audit verified that all fee, admission, and calendar figures apply specifically to academic year `2026-2027`. Historical pages (e.g. 2024-2025) must remain flagged as `archived` or excluded to prevent retrieval confusion.
2. **Entity Harmonization**: Course codes across department catalogs were standardized to 5 alphanumeric characters (e.g., `CS101`, `AI201`) to align with graph entity keys.
3. **Approval Gating**: Content mapped above will be ingested into `knowledge/staging/` before administrative sign-off transitions records to `knowledge/approved/`.
