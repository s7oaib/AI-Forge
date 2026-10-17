"""Unit tests for staging quarantine workflow."""

import pytest
from datetime import date
from pathlib import Path
import yaml

from src.governance.ingest_staging import audit_quarantine, promote_to_approved, StagingQuarantineError


def test_quarantine_audit_clean(tmp_path):
    staging_dir = tmp_path / "staging"
    approved_dir = tmp_path / "approved"
    staging_dir.mkdir()
    approved_dir.mkdir()
    
    clean, issues = audit_quarantine(staging_path=staging_dir, approved_path=approved_dir)
    assert clean is True
    assert len(issues) == 0


def test_quarantine_audit_detects_leak(tmp_path):
    staging_dir = tmp_path / "staging"
    approved_dir = tmp_path / "approved"
    staging_dir.mkdir()
    approved_dir.mkdir()
    
    # Create an unapproved/pending file in approved directory
    leaked_file = approved_dir / "unapproved.md"
    content = """---
id: DOC-LEAK-001
title: Leaked Pending Document
category: admissions
slug: leaked-pending
official_url: https://greenfield.edu/leak
source_retrieval_date: 2026-10-17
approval_status: pending
last_verified_date: 2026-10-17
effective_academic_year: 2026-2027
version: 1.0.0
---
Leaked content that was never approved.
"""
    leaked_file.write_text(content, encoding="utf-8")
    
    clean, issues = audit_quarantine(staging_path=staging_dir, approved_path=approved_dir)
    assert clean is False
    assert any("CRITICAL LEAK" in issue for issue in issues)


def test_promote_to_approved_workflow(tmp_path):
    staging_dir = tmp_path / "staging"
    approved_dir = tmp_path / "approved"
    staging_dir.mkdir()
    approved_dir.mkdir()
    
    staging_file = staging_dir / "new_course.md"
    content = """---
id: DOC-CRS-TEST
title: Test Course Title
category: courses
slug: test-course
official_url: https://greenfield.edu/academics/courses/test
source_retrieval_date: 2026-10-17
approval_status: pending
last_verified_date: 2026-10-17
effective_academic_year: 2026-2027
version: 1.0.0
---
# Course Body Description
Details of the course.
"""
    staging_file.write_text(content, encoding="utf-8")
    
    # Promote
    promoted_path = promote_to_approved(
        staging_file=staging_file,
        approver="provost-desk@greenfield.edu",
        approved_dir=approved_dir
    )
    
    assert promoted_path.exists()
    assert not staging_file.exists()
    assert promoted_path.parent.name == "courses"
    
    # Verify promoted content has approved metadata
    promoted_text = promoted_path.read_text(encoding="utf-8")
    assert "approval_status: approved" in promoted_text
    assert "approved_by: provost-desk@greenfield.edu" in promoted_text
    assert f"approval_date: '{date.today().isoformat()}'" in promoted_text or f"approval_date: {date.today().isoformat()}" in promoted_text
