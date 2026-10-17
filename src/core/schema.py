"""Core schemas and configuration models for College Information Chatbot."""

from datetime import date
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class ApprovalStatus(str, Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class KnowledgeCategory(str, Enum):
    PROFILE = "profile"
    DEPARTMENTS = "departments"
    PROGRAMS = "programs"
    COURSES = "courses"
    FACULTY = "faculty"
    ADMISSIONS = "admissions"
    FEES_SCHOLARSHIPS = "fees_scholarships"
    PLACEMENTS = "placements"
    ACADEMICS = "academics"
    FACILITIES = "facilities"
    CAMPUS_LIFE = "campus_life"
    FAQS = "faqs"


class EntityReference(BaseModel):
    id: str = Field(..., description="Unique entity ID, e.g., FAC-CSE-042 or DEPT-CSE")
    type: str = Field(..., description="Entity type, e.g., Person, Department, Course")
    name: str = Field(..., description="Canonical display name of entity")


class RelationshipReference(BaseModel):
    source: str = Field(..., description="Source entity ID")
    relation: str = Field(..., description="Directed relationship predicate, e.g., TEACHES, HEAD_OF")
    target: str = Field(..., description="Target entity ID")


class DocumentFrontmatter(BaseModel):
    """Authoritative frontmatter schema for approved college markdown documents."""
    id: str = Field(..., description="Unique document/record ID, e.g., DOC-ADM-001")
    title: str = Field(..., min_length=3, description="Canonical title of the document")
    category: KnowledgeCategory = Field(..., description="One of the 12 institutional categories")
    slug: str = Field(..., description="URL-friendly slug")
    official_url: str = Field(..., description="Official college website URL corresponding to this record")
    source_retrieval_date: date = Field(..., description="Date content was retrieved from official website")
    approval_status: ApprovalStatus = Field(..., description="Approval status: approved, pending, rejected, archived")
    approved_by: Optional[str] = Field(None, description="Email or ID of designated college administrator")
    approval_date: Optional[date] = Field(None, description="Date administrator approved the document")
    last_verified_date: date = Field(..., description="Date facts were last verified against official records")
    effective_academic_year: str = Field(..., pattern=r"^\d{4}-\d{4}$", description="Academic year formatted as YYYY-YYYY, e.g. 2026-2027")
    review_before_date: Optional[date] = Field(None, description="Expiry or re-verification deadline")
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$", description="SemVer string")
    entities: List[EntityReference] = Field(default_factory=list, description="Explicit entity references")
    relationships: List[RelationshipReference] = Field(default_factory=list, description="Explicit graph edges")
    keywords: List[str] = Field(default_factory=list, description="Aliases and search keywords")

    @field_validator("approved_by")
    @classmethod
    def validate_approver_when_approved(cls, v, info):
        status = info.data.get("approval_status")
        if status == ApprovalStatus.APPROVED and not v:
            raise ValueError("approved_by must be specified when approval_status is 'approved'")
        return v

    @field_validator("approval_date")
    @classmethod
    def validate_approval_date_when_approved(cls, v, info):
        status = info.data.get("approval_status")
        if status == ApprovalStatus.APPROVED and not v:
            raise ValueError("approval_date must be specified when approval_status is 'approved'")
        return v
