"""Unit tests for DocumentFrontmatter schema and governance validation."""

import pytest
from datetime import date
from pydantic import ValidationError

from src.core.schema import DocumentFrontmatter, ApprovalStatus, KnowledgeCategory
from src.governance.validator import extract_frontmatter, validate_markdown_file


def test_valid_document_frontmatter():
    """Verify that a well-formed approved document frontmatter passes validation."""
    data = {
        "id": "DOC-ADM-001",
        "title": "B.Tech Undergraduate Admissions Eligibility",
        "category": "admissions",
        "slug": "ug-admissions-eligibility",
        "official_url": "https://college.edu/admissions/btech",
        "source_retrieval_date": "2026-10-15",
        "approval_status": "approved",
        "approved_by": "administrator@college.edu",
        "approval_date": "2026-10-16",
        "last_verified_date": "2026-10-16",
        "effective_academic_year": "2026-2027",
        "review_before_date": "2027-06-30",
        "version": "1.0.0",
        "keywords": ["admissions", "eligibility", "btech", "criteria"]
    }
    model = DocumentFrontmatter(**data)
    assert model.id == "DOC-ADM-001"
    assert model.category == KnowledgeCategory.ADMISSIONS
    assert model.approval_status == ApprovalStatus.APPROVED
    assert model.approved_by == "administrator@college.edu"


def test_missing_required_id():
    """Verify that omitting the unique ID raises a validation error."""
    data = {
        "title": "Incomplete Document",
        "category": "profile",
        "slug": "incomplete-doc",
        "official_url": "https://college.edu/about",
        "source_retrieval_date": "2026-10-15",
        "approval_status": "pending",
        "last_verified_date": "2026-10-15",
        "effective_academic_year": "2026-2027",
    }
    with pytest.raises(ValidationError) as exc_info:
        DocumentFrontmatter(**data)
    assert "id" in str(exc_info.value)


def test_invalid_category():
    """Verify that an undefined knowledge category raises a validation error."""
    data = {
        "id": "DOC-INVALID-001",
        "title": "Invalid Category Document",
        "category": "sports_betting",  # Not in 12 defined categories
        "slug": "invalid-category",
        "official_url": "https://college.edu/sports",
        "source_retrieval_date": "2026-10-15",
        "approval_status": "pending",
        "last_verified_date": "2026-10-15",
        "effective_academic_year": "2026-2027",
    }
    with pytest.raises(ValidationError) as exc_info:
        DocumentFrontmatter(**data)
    assert "category" in str(exc_info.value)


def test_invalid_academic_year_format():
    """Verify that effective_academic_year must conform to YYYY-YYYY."""
    data = {
        "id": "DOC-ADM-002",
        "title": "Admissions Cutoffs",
        "category": "admissions",
        "slug": "cutoffs",
        "official_url": "https://college.edu/cutoffs",
        "source_retrieval_date": "2026-10-15",
        "approval_status": "pending",
        "last_verified_date": "2026-10-15",
        "effective_academic_year": "2026",  # Invalid, should be 2026-2027
    }
    with pytest.raises(ValidationError) as exc_info:
        DocumentFrontmatter(**data)
    assert "effective_academic_year" in str(exc_info.value)


def test_approved_status_requires_approver():
    """Verify that approval_status='approved' strictly requires approved_by and approval_date."""
    data = {
        "id": "DOC-FEE-001",
        "title": "Fee Structure 2026",
        "category": "fees_scholarships",
        "slug": "fee-structure",
        "official_url": "https://college.edu/fees",
        "source_retrieval_date": "2026-10-15",
        "approval_status": "approved",
        "approved_by": None,  # Missing approver!
        "approval_date": None,
        "last_verified_date": "2026-10-15",
        "effective_academic_year": "2026-2027",
    }
    with pytest.raises(ValidationError) as exc_info:
        DocumentFrontmatter(**data)
    assert "approved_by must be specified" in str(exc_info.value)


def test_extract_frontmatter_helper():
    """Verify frontmatter delimiter parsing."""
    raw = """---
id: "TEST-01"
title: "Test Title"
---
# Actual Markdown Heading
Some text.
"""
    data, body, err = extract_frontmatter(raw)
    assert err is None
    assert data["id"] == "TEST-01"
    assert "Actual Markdown Heading" in body


def test_validate_markdown_file_with_warnings(tmp_path):
    """Verify that an expired or pending document is flagged with warnings."""
    test_file = tmp_path / "pending_expired.md"
    content = """---
id: "DOC-EXP-001"
title: "Expired Policy Document"
category: "academics"
slug: "expired-policy"
official_url: "https://college.edu/policy"
source_retrieval_date: "2024-01-01"
approval_status: "pending"
last_verified_date: "2024-01-01"
effective_academic_year: "2024-2025"
review_before_date: "2025-01-01"
---
# Expired Regulations
Old content.
"""
    test_file.write_text(content, encoding="utf-8")
    
    # Validate with reference date in 2026
    res = validate_markdown_file(str(test_file), reference_date=date(2026, 10, 17))
    assert res.is_valid is True
    assert len(res.errors) == 0
    # Should have 2 warnings: pending status + expired date
    assert any("not approved" in w for w in res.warnings)
    assert any("has expired" in w for w in res.warnings)
