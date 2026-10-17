"""Graphify extraction configuration for academic-domain knowledge.

Declares the node/edge vocabulary consumed by the build pipeline. When the
Graphify CLI is available it is used for LLM-facilitated extraction; the
deterministic fallback builds the graph directly from approved frontmatter.
"""

EDGE_VOCAB = {
    "OFFERS_PROGRAM": "A department offers a degree program.",
    "INCLUDES_COURSE": "A program/curriculum includes a course.",
    "TAUGHT_BY": "A course is taught by a faculty member.",
    "TEACHES": "A faculty member teaches a course.",
    "HEAD_OF": "A faculty member heads a lab/centre/department.",
    "HOD_OF": "A faculty member is Head of Department.",
    "PREREQUISITE_FOR": "A course is a prerequisite for another course.",
    "LOCATED_AT": "An entity is located in a building/block/facility.",
    "ELIGIBILITY_FOR": "An admission rule makes an entity eligible for a program/branch.",
    "MEMBER_OF": "A faculty member belongs to a department.",
    "HOSTS": "A department hosts a research centre/lab.",
    "PRACTICUM_AT": "A course conducts its practicals in a lab.",
    "CONDUCTS": "A department conducts a placement/visit event.",
}

STRUCTURAL_EDGES = {"HAS_DEPARTMENT", "PART_OF", "CATEGORY_OF"}

NODE_TYPES = {
    "College",
    "Department",
    "Program",
    "Course",
    "Faculty",
    "Facility",
    "Recruiter",
    "Event",
    "Organization",
    "Building",
    "Lab",
    "Undefined",
}

STRUCTURAL_RULES = [
    {"relation": "HAS_DEPARTMENT", "source_type": "College", "target_type": "Department"},
    {"relation": "PART_OF", "source_type": "Faculty", "target_type": "Department"},
]

DEFAULT_GRAPH_PATH = "artifacts/graph/graph.json"
