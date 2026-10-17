"""Seed script: generates the initial authoritative Markdown knowledge base.

All records are synthetic institutional fixtures for Greenfield College so the
pipeline is testable end-to-end before real governance data arrives. Every
record is written through DocumentFrontmatter, so a seeding run cannot produce
schema-invalid output.

Run:  python -m src.admin.seed_demo_knowledge
"""

import argparse
from pathlib import Path
import yaml

from src.core.schema import DocumentFrontmatter

APPROVED_DIR = Path("knowledge/approved")
APPROVER = "provost-desk@greenfield.edu"

_DATE_RETRIEVED = "2026-10-15"
_DATE_APPROVED = "2026-10-16"
_REVIEW_BEFORE = "2027-06-30"


def _fm(doc_id, title, category, slug, url, entities, relationships, keywords):
    return {
        "id": doc_id,
        "title": title,
        "category": category,
        "slug": slug,
        "official_url": url,
        "source_retrieval_date": _DATE_RETRIEVED,
        "approval_status": "approved",
        "approved_by": APPROVER,
        "approval_date": _DATE_APPROVED,
        "last_verified_date": _DATE_APPROVED,
        "effective_academic_year": "2026-2027",
        "review_before_date": _REVIEW_BEFORE,
        "entities": entities,
        "relationships": relationships,
        "keywords": keywords,
    }


def _e(eid, etype, name):
    return {"id": eid, "type": etype, "name": name}


def _r(source, relation, target):
    return {"source": source, "relation": relation, "target": target}


RECORDS = [
    (
        "profile/college_overview.md",
        _fm(
            "DOC-PRO-001",
            "Greenfield College of Engineering: Overview",
            "profile",
            "college-overview",
            "https://greenfield.edu/about",
            [_e("COL-CORE", "College", "Greenfield College of Engineering")],
            [],
            [
                "overview",
                "about",
                "history",
                "established",
                "founded",
                "greenfield",
            ],
        ),
        """# Greenfield College of Engineering

## Institutional Profile
- **Established**: 1998 as an autonomous engineering college
- **Location**: Greenfield City, Survey No 42, University Road
- **Type**: Aided, co-educational institution
- **Accreditation**: NBA accredited and NAAC 'A++' grade (2025 cycle)

## Key Statistics
- Total enrolled students: about 4,200
- Faculty strength: about 280 full-time members
- Campus area: 42 acres with library, hostels, and sports complex

## Contact
- General inquiries: info@greenfield.edu
- Admissions office: admissions@greenfield.edu
- Phone (working hours 9:00 to 17:00): +91-80-4000-1000
""",
    ),
    (
        "departments/cse.md",
        _fm(
            "DOC-DEP-CSE",
            "Department of Computer Science and Engineering",
            "departments",
            "department-cse",
            "https://greenfield.edu/departments/cse",
            [
                _e("DEPT-CSE", "Department", "Computer Science and Engineering"),
                _e("FAC-LTRC", "Facility", "Language Technologies Research Center"),
            ],
            [
                _r("DEPT-CSE", "LOCATED_AT", "BLK-TECH"),
                _r("DEPT-CSE", "HOSTS", "FAC-LTRC"),
            ],
            [
                "cse",
                "computer science",
                "department",
                "ltrc",
                "language technologies",
                "research center",
            ],
        ),
        """# Department of Computer Science and Engineering

## Overview
The Department of Computer Science and Engineering (CSE) offers B.Tech,
M.Tech, and Ph.D. programs and hosts the Language Technologies Research
Center (LTRC), the college's NLP and speech research laboratory.

## Department Highlights
- Founded: 1998
- Faculty count: about 65 members
- Laboratories: LTRC, Software Engineering Lab, Systems Lab, AI/ML Lab
- Location: Tech Block (BLK-TECH), second floor

## Research Centres
- **Language Technologies Research Center (LTRC)**: headed by Dr. Arvind Raman
- Head of Department: Prof. Suresh Iyer since 2021

## Contact
- Department office: cse-office@greenfield.edu
- Phone (Tech Block): +91-80-4000-1234
""",
    ),
    (
        "departments/ece.md",
        _fm(
            "DOC-DEP-ECE",
            "Department of Electronics and Communication Engineering",
            "departments",
            "department-ece",
            "https://greenfield.edu/departments/ece",
            [_e("DEPT-ECE", "Department", "Electronics and Communication Engineering")],
            [_r("DEPT-ECE", "LOCATED_AT", "BLK-NULL-2")],
            ["ece", "electronics", "communication", "department", "vlsi"],
        ),
        """# Department of Electronics and Communication Engineering

## Overview
The Department of Electronics and Communication Engineering offers B.Tech
and M.Tech programs with VLSI, Embedded Systems, and Signal Processing
specializations.

## Key Facts
- Faculty count: about 48 members
- Laboratories: VLSI Design Lab, Embedded Systems Lab, RF Lab
- Location: Nulliplex Block 2 (BLK-NULL-2), first floor
- Head of Department: Dr. Anjali Verma since 2022
- Department office: ece-office@greenfield.edu
""",
    ),
    (
        "departments/mechanical.md",
        _fm(
            "DOC-DEP-ME",
            "Department of Mechanical Engineering",
            "departments",
            "department-mechanical",
            "https://greenfield.edu/departments/mech",
            [_e("DEPT-ME", "Department", "Mechanical Engineering")],
            [_r("DEPT-ME", "LOCATED_AT", "BLK-NPT")],
            ["mechanical", "mech", "department", "thermodynamics"],
        ),
        """# Department of Mechanical Engineering

## Overview
The Department of Mechanical Engineering (ME) offers B.Tech and M.Tech
programs across design, thermal, and manufacturing specializations.

## Key Facts
- Faculty count: about 40 members
- Laboratories: CAD/CAM Lab, Thermal Engineering Lab, Machine Shop
- Location: North Production Block
- Head of Department: Dr. Ravi Menon since 2020
- Department office: mech-office@greenfield.edu
""",
    ),
    (
        "programs/btech.md",
        _fm(
            "DOC-PRG-BTECH",
            "Bachelor of Technology (B.Tech) Program",
            "programs",
            "btech-program",
            "https://greenfield.edu/programs/btech",
            [_e("PRG-BTECH", "Program", "B.Tech Program")],
            [
                _r("DEPT-CSE", "OFFERS_PROGRAM", "PRG-BTECH"),
                _r("DEPT-ECE", "OFFERS_PROGRAM", "PRG-BTECH"),
                _r("DEPT-ME", "OFFERS_PROGRAM", "PRG-BTECH"),
            ],
            ["b.tech", "btech", "undergraduate", "bachelor", "ug program"],
        ),
        """# Bachelor of Technology (B.Tech)

## Program Structure
- Duration: 8 semesters (4 years), full time
- Intake branches: Computer Science and Engineering, Electronics and
  Communication Engineering, Mechanical Engineering
- Degree awarded on completion of 160 credits under the CGPA scheme

## B.Tech Computer Science and Engineering
- Intake capacity: 120 seats
- Includes core electives such as CS402 Natural Language Processing and
  CS301 Machine Learning in the senior year

## B.Tech Electronics and Communication Engineering
- Intake capacity: 90 seats

## B.Tech Mechanical Engineering
- Intake capacity: 90 seats
""",
    ),
    (
        "programs/mtech.md",
        _fm(
            "DOC-PRG-MTECH",
            "Master of Technology (M.Tech) Program",
            "programs",
            "mtech-program",
            "https://greenfield.edu/programs/mtech",
            [_e("PRG-MTECH", "Program", "M.Tech Program")],
            [
                _r("DEPT-CSE", "OFFERS_PROGRAM", "PRG-MTECH"),
                _r("DEPT-ECE", "OFFERS_PROGRAM", "PRG-MTECH"),
            ],
            ["m.tech", "mtech", "postgraduate", "masters", "pg program"],
        ),
        """# Master of Technology (M.Tech)

## Program Structure
- Duration: 4 semesters (2 years), full time
- Offered by: Computer Science and Engineering (specialization in
  Artificial Intelligence and Data Science) and Electronics and
  Communication Engineering (specialization in VLSI Design)
- Admission through the GATE examination score

## M.Tech Computer Science and Engineering
- Intake capacity: 36 seats
- Thesis work is hosted at LTRC for AI specializations
""",
    ),
    (
        "courses/cs402_nlp.md",
        _fm(
            "DOC-CRS-CS402",
            "CS402 Natural Language Processing",
            "courses",
            "cs402-nlp",
            "https://greenfield.edu/courses/CS402",
            [
                _e("CRS-CS402", "Course", "CS402 Natural Language Processing"),
                _e("LAB-NLP", "Facility", "NLP Lab at LTRC"),
            ],
            [
                _r("CRS-CS402", "TAUGHT_BY", "FAC-001"),
                _r("CRS-CS402", "PREREQUISITE_FOR", "CRS-CS0"),
                _r("CRS-CS402", "PRACTICUM_AT", "LAB-NLP"),
            ],
            [
                "nlp",
                "natural language processing",
                "cs402",
                "course",
                "elective",
                "text processing",
            ],
        ),
        """# CS402: Natural Language Processing

## Course Details
- Course code: CS402
- Semester: 7th semester, B.Tech Computer Science and Engineering
- Credits: 3 lecture + 1 practicum
- Instructor: Dr. Arvind Raman, who also heads the Language
  Technologies Research Center (LTRC)
- Practicum sessions are held in the NLP Lab at LTRC

## Syllabus
- 1. Tokenization, stemming, lemmatization
- 2. Syntactic parsing and part-of-speech tagging
- 3. Word and sentence embeddings
- 4. Text classification and information retrieval
- 5. Large language models and prompt engineering

## Assessment
- Mid-semester exam: 30%
- End-semester exam: 40%
- Lab assignments: 30%
""",
    ),
    (
        "courses/cs301_ml.md",
        _fm(
            "DOC-CRS-CS301",
            "CS301 Machine Learning",
            "courses",
            "cs301-ml",
            "https://greenfield.edu/courses/CS301",
            [_e("CRS-CS301", "Course", "CS301 Machine Learning")],
            [
                _r("CRS-CS301", "TAUGHT_BY", "FAC-003"),
                _r("CRS-CS301", "PREREQUISITE_FOR", "CRS-CS402"),
            ],
            [
                "machine learning",
                "cs301",
                "ml",
                "course",
                "core course",
            ],
        ),
        """# CS301: Machine Learning

## Course Details
- Course code: CS301
- Semester: 6th semester, B.Tech Computer Science and Engineering
- Credits: 3 lecture + 1 lab
- Instructor: Dr. Kamala Devi (FAC-003)
- CS301 Machine Learning is the prerequisite for CS402 Natural
  Language Processing

## Syllabus
- 1. Linear models and optimization
- 2. Neural networks and backpropagation
- 3. Ensemble methods
- 4. Evaluation methodology
""",
    ),
    (
        "faculty/arvind_raman.md",
        _fm(
            "DOC-FAC-001",
            "Faculty Profile: Dr. Arvind Raman",
            "faculty",
            "faculty-arvind-raman",
            "https://greenfield.edu/departments/cse/faculty/arvind-raman",
            [
                _e("FAC-001", "Faculty", "Dr. Arvind Raman"),
            ],
            [
                _r("FAC-001", "MEMBER_OF", "DEPT-CSE"),
                _r("FAC-001", "TEACHES", "CRS-CS402"),
                _r("FAC-001", "HEAD_OF", "FAC-LTRC"),
            ],
            [
                "arvind raman",
                "professor",
                "nlp",
                "faculty",
                "ltrc",
                "cs402",
            ],
        ),
        """# Faculty Profile: Dr. Arvind Raman

## Designation & Department
- Position: Professor
- Department: Computer Science and Engineering
- Office Location: Tech Block, Room 402
- Email: arvind.raman@greenfield.edu

## Academic Leadership
- Since 2019, Dr. Arvind Raman has headed the Language Technologies
  Research Center (LTRC), the NLP laboratory of the CSE department.
- Dr. Arvind Raman teaches CS402 Natural Language Processing.

## Educational Qualifications
- Ph.D. in Computational Linguistics, Bengaluru Institute of Science, 2004
- M.Tech in Computer Science, 1999

## Research Interests
- Enterprise retrieval-augmented generation
- Low-resource language modelling
- Conversational information systems
""",
    ),
    (
        "faculty/anjali_verma.md",
        _fm(
            "DOC-FAC-002",
            "Faculty Profile: Dr. Anjali Verma",
            "faculty",
            "faculty-anjali-verma",
            "https://greenfield.edu/departments/ece/faculty/anjali-verma",
            [_e("FAC-002", "Faculty", "Dr. Anjali Verma")],
            [_r("FAC-002", "MEMBER_OF", "DEPT-ECE"), _r("FAC-002", "TEACHES", "CRS-EC401")],
            ["anjali verma", "vlsi", "faculty", "ece", "professor"],
        ),
        """# Faculty Profile: Dr. Anjali Verma

## Designation & Department
- Position: Professor and Head of Department (ECE, since 2022)
- Department: Electronics and Communication Engineering
- Office Location: Nulliplex Block 2, Room 105
- Email: anjali.verma@greenfield.edu

## Teaching
- Dr. Anjali Verma teaches EC401 VLSI Circuit Design.

## Research Interests
- Low-power digital design, semiconductor device technology
""",
    ),
    (
        "faculty/kamala_devi.md",
        _fm(
            "DOC-FAC-003",
            "Faculty Profile: Dr. Kamala Devi",
            "faculty",
            "faculty-kamala-devi",
            "https://greenfield.edu/departments/cse/faculty/kamala-devi",
            [_e("FAC-003", "Faculty", "Dr. Kamala Devi")],
            [_r("FAC-003", "MEMBER_OF", "DEPT-CSE"), _r("FAC-003", "TEACHES", "CRS-CS301")],
            ["kamala devi", "machine learning", "faculty", "cs301", "professor"],
        ),
        """# Faculty Profile: Dr. Kamala Devi

## Designation & Department
- Position: Associate Professor
- Department: Computer Science and Engineering
- Office Location: Tech Block, Room 214
- Email: kamala.devi@greenfield.edu

## Teaching
- Dr. Kamala Devi teaches CS301 Machine Learning.

## Research Interests
- Optimization, reinforcement learning, trustworthy ML
""",
    ),
    (
        "admissions/btech_admission_criteria.md",
        _fm(
            "DOC-ADM-CRIT",
            "B.Tech Admission Criteria and Cutoffs (2026-2027)",
            "admissions",
            "btech-admission-criteria",
            "https://greenfield.edu/admissions/btech-criteria",
            [_e("PRG-BTECH", "Program", "B.Tech Program")],
            [_r("PRG-BTECH", "ELIGIBILITY_FOR", "DEPT-CSE")],
            [
                "admission",
                "eligibility",
                "cutoff",
                "jee",
                "intake",
                "b.tech",
                "apply",
                "application",
            ],
        ),
        """# B.Tech Admission Criteria and Cutoffs (2026-2027)

## Eligibility
- Completion of 10+2 with Physics, Chemistry, Mathematics
- Minimum aggregate: 60 percent in PCM
- Valid JEE Main score

## Cutoffs (2026 admissions round)
- B.Tech Computer Science and Engineering: 93 percentile (closing rank 3,900)
- B.Tech Electronics and Communication Engineering: 88 percentile
- B.Tech Mechanical Engineering: 79 percentile

## Intake Capacity
- CSE: 120 seats | ECE: 90 seats | ME: 90 seats

## Application Process
- Online application window: 1 April to 15 June
- Score card, fee payment, category certificate where applicable
""",
    ),
    (
        "fees_scholarships/btech_fees_2026.md",
        _fm(
            "DOC-FEE-BTECH",
            "B.Tech Fee Schedule and Scholarships (2026-2027)",
            "fees_scholarships",
            "btech-fees-2026-2027",
            "https://greenfield.edu/fees/btech",
            [_e("PRG-BTECH", "Program", "B.Tech Program")],
            [],
            [
                "fees",
                "tuition",
                "scholarship",
                "waiver",
                "installment",
                "payment",
                "cost",
            ],
        ),
        """# B.Tech Fee Schedule and Scholarships (2026-2027)

## Annual Tuition (per academic year 2026-2027)
- B.Tech Computer Science and Engineering: 145,000 rupees
- B.Tech Electronics and Communication Engineering: 138,000 rupees
- B.Tech Mechanical Engineering: 132,000 rupees
- Other charges: 12,000 rupees per year (library, exam, and activity fees)

## Payment Rules
- Two installments: 60 percent at registration, 40 percent by 15 January
- Late payment surcharge: 2 percent after the due date

## Scholarships
- Merit waiver: 25 percent tuition waiver for the top 5 percent of first-year
  JEE scorers in each branch
- Need-based grant: up to 50 percent waiver for verified family income
  below 3 lakh rupees per year
""",
    ),
    (
        "placements/placement_report_2026.md",
        _fm(
            "DOC-PLC-2026",
            "Campus Placement Report (2025-2026)",
            "placements",
            "placement-report-2025-2026",
            "https://greenfield.edu/placements/report-2026",
            [_e("REC-INFO", "Recruiter", "InfoTech Systems Ltd"), _e("REC-VOL", "Recruiter", "Voltrodyne Motors")],
            [
                _r("DEPT-CSE", "CONDUCTS", "PI Visit"),
            ],
            [
                "placement",
                "recruiters",
                "salary",
                "ctc",
                "package",
                "campus",
                "companies",
            ],
        ),
        """# Campus Placement Report (2025-2026)

## Headline Statistics
- Placement percentage: 92 percent of registered students
- Median CTC: 8.5 lakh rupees per annum
- Highest package offered on campus: 42 lakh rupees per annum
- Participating recruiters: 190 companies

## Sector Recruiters
- Software: InfoTech Systems Ltd, Quantify Analytics Pvt Ltd
- Core engineering: Voltrodyne Motors, DeltaFab Industries
- Electronics: Silicore Semiconductors

## Hiring Funnel
- Eligibility screen: minimum 6.0 CGPA
- Campus interviews conducted during September-February
""",
    ),
    (
        "academics/grading_system.md",
        _fm(
            "DOC-ACA-GRD",
            "Academic Grading System",
            "academics",
            "grading-system",
            "https://greenfield.edu/academics/grading",
            [],
            [],
            ["grading", "cgpa", "gpa", "grades", "evaluation", "marks"],
        ),
        """# Academic Grading System

## Scheme
- 10-point Cumulative Grade Point Average (CGPA) scale
- Grades: S(10), A(9), B(8), C(7), D(6), E(5), P(4), F(0)

## Convocation Rules
- Minimum pass: letter grade P or above in every course
- First class with distinction: CGPA 8.5 or above
- Degree awarded after clearing all 160 B.Tech credits
- One backlog re-examination allowed per subject per semester
""",
    ),
    (
        "academics/academic_calendar.md",
        _fm(
            "DOC-ACA-CAL",
            "Academic Calendar (2026-2027)",
            "academics",
            "academic-calendar-2026-2027",
            "https://greenfield.edu/academics/calendar",
            [],
            [],
            [
                "calendar",
                "semester dates",
                "holidays",
                "exam schedule",
                "start",
                "registration",
            ],
        ),
        """# Academic Calendar (2026-2027)

## Odd Semester (Semester 1 and 5 of even batches)
- Registration: 20 July 2026
- Classes begin: 21 July 2026
- Mid-semester examinations: 21-26 September 2026
- End-semester examinations: 30 November to 12 December 2026
- Winter vacation: 13 December 2026 to 4 January 2027

## Even Semester
- Classes begin: 5 January 2027
- End-semester examinations: 26 April to 8 May 2027

## Library And Hostel Notes
- Library hours extend to 23:00 during examination weeks
- Hostels open on 19 July 2026 for the odd semester
""",
    ),
    (
        "facilities/library.md",
        _fm(
            "DOC-FAC-LIB",
            "Central Library Facilities",
            "facilities",
            "central-library",
            "https://greenfield.edu/facilities/library",
            [_e("FAC-LIB", "Facility", "Central Library")],
            [_r("FAC-LIB", "LOCATED_AT", "BLK-LIB")],
            [
                "library",
                "hours",
                "books",
                "reading room",
                "timings",
                "open",
            ],
        ),
        """# Central Library

## Timings
- Weekdays (Monday-Friday): 8:00 to 22:00
- Saturdays: 9:00 to 17:00
- Sundays and public holidays: closed
- During examination weeks: 8:00 to 23:00

## Collection
- Volume count: about 85,000
- Subscriptions: 240 technical journals and digital archives
- Reading room capacity: 500 seats

## Location
- Central Library is in the Library Block (BLK-LIB), adjacent to Tech Block

## Services
- Loan limit: 6 books for 14 days (faculty 20 books for 30 days)
""",
    ),
    (
        "facilities/hostels.md",
        _fm(
            "DOC-FAC-HST",
            "Hostel Facilities",
            "facilities",
            "hostel-facilities",
            "https://greenfield.edu/facilities/hostels",
            [_e("HOS-GANGA", "Facility", "Ganga Hostel")],
            [],
            [
                "hostel",
                "accommodation",
                "residence",
                "mess",
                "boarding",
                "rooms",
            ],
        ),
        """# Hostel Facilities

## Overview
- Hostel capacity: about 2,400 students in five residential blocks
- Blocks: Ganga, Narmada, Shivani, Nilgiri, and Yamuna hostels
- Mess: vegetarian and non-vegetarian common messes, monthly meal plan

## Rooms And Amenities
- Double and triple occupancy rooms; single rooms for final-year toppers
- 24x7 staff medical room, common reading halls, and gym access
- Wired internet in rooms, wi-fi in common areas

## Application
- Hostel allotment confirmed at registration; wardens office hours are
  10:00 to 13:00 on working days
- Student relations desk: hostels-office@greenfield.edu
""",
    ),
    (
        "campus_life/clubs.md",
        _fm(
            "DOC-CLB-LIST",
            "Student Clubs and Chapters",
            "campus_life",
            "student-clubs",
            "https://greenfield.edu/campus-life/clubs",
            [_e("CLB-ACM", "Organization", "ACM Student Chapter"), _e("CLB-CHESS", "Organization", "Chess Club")],
            [],
            [
                "clubs",
                "student chapters",
                "acm",
                "chess",
                "societies",
                "extracurricular",
            ],
        ),
        """# Student Clubs and Chapters

## Registered Student Bodies
- **ACM Student Chapter**: professional computing society, meets every
  second Friday, organizes coding contests
- **Chess Club**: weekly meetings Wednesdays 17:30-20:00 in the Student
  Activity Center; hosts the college rapid championship each February
- Rotaract, Eco Warriors, Music Society, and Robotics Guild

## Registration
- New members register during the clubs fair in the third week of August
- Every club requires a faculty moderator and a minimum of 20 members
""",
    ),
    (
        "campus_life/techfest_prism.md",
        _fm(
            "DOC-CLB-PRISM",
            "TechFest Prism",
            "campus_life",
            "techfest-prism",
            "https://greenfield.edu/campus-life/prism",
            [_e("EVT-PRISM", "Event", "TechFest Prism")],
            [],
            ["prism", "techfest", "festival", "events", "hackathon"],
        ),
        """# TechFest Prism

## Overview
- Flagship national technical festival of Greenfield College
- Held annually in the second week of March
- Events: 36-hour hackathon, robotics arena, paper contests, and
  startup pitch night

## Participation
- Open to all colleges; per-team registration fee of 900 rupees
- Organized by the student council with faculty mentors
""",
    ),
    (
        "faqs/general_faq.md",
        _fm(
            "DOC-FAQ-GEN",
            "General Frequently Asked Questions",
            "faqs",
            "general-faq",
            "https://greenfield.edu/faq",
            [],
            [],
            [
                "faq",
                "questions",
                "contact",
                "phone",
                "email",
                "help",
                "principal",
            ],
        ),
        """# General Frequently Asked Questions

## Frequently Asked Questions

### How do I contact the college?
The main switchboard is +91-80-4000-1000 (working hours 9:00-17:00).
Email: info@greenfield.edu; admissions: admissions@greenfield.edu.

### When does the academic session start?
Registration is 20 July 2026 and classes begin 21 July 2026.

### Where is the principal?
The principal's current appointment details are maintained on the
official website directory; the chatbot does not answer individual
administrative contacts that are not in this knowledge base.
""",
    ),
]


def seed(base_dir: Path = APPROVED_DIR) -> int:
    written = 0
    for relpath, fm, body in RECORDS:
        model = DocumentFrontmatter(**fm)
        target: Path = base_dir / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = ["---"]
        dump = {
            "id": model.id,
            "title": model.title,
            "category": model.category.value,
            "slug": model.slug,
            "official_url": model.official_url,
            "source_retrieval_date": model.source_retrieval_date.isoformat(),
            "approval_status": model.approval_status.value,
            "approved_by": model.approved_by,
            "approval_date": model.approval_date.isoformat(),
            "last_verified_date": model.last_verified_date.isoformat(),
            "effective_academic_year": model.effective_academic_year,
            "review_before_date": (
                model.review_before_date.isoformat() if model.review_before_date else None
            ),
            "version": model.version,
            "entities": [
                {"id": e.id, "type": e.type, "name": e.name} for e in model.entities
            ],
            "relationships": [dict(r) for r in model.relationships],
            "keywords": list(model.keywords),
        }
        if dump["review_before_date"] is None:
            dump.pop("review_before_date")
        lines = ["---", yaml.safe_dump(dump, sort_keys=False, default_flow_style=False).rstrip("\n"), "---", "", body.rstrip("\n"), ""]
        target.write_text("\n".join(lines), encoding="utf-8")
        written += 1
    return written


def main():
    parser = argparse.ArgumentParser(
        description="Seed the synthetic authoritative knowledge base"
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing records")
    args = parser.parse_args()
    count = seed()
    print(f"Seeded {count} approved records under knowledge/approved/")
    if args.force:
        print("Note: --force accepted; existing records were overwritten by design reseed.")


if __name__ == "__main__":
    main()
