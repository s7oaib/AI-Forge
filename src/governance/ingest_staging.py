"""Staging quarantine workflow for College Information Chatbot.

Enforces Principle 3 (Strict Governance Gate) of the Constitution:
- Ingestion occurs strictly into knowledge/staging/
- Zero staging or pending documents may ever enter knowledge/approved/ or production indexes
- Administrative promotion requires schema validation, designated approver ID, and approval date.
"""

import argparse
import os
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml

from src.core.schema import ApprovalStatus, DocumentFrontmatter
from src.governance.validator import extract_frontmatter, validate_markdown_file


STAGING_DIR = Path("knowledge/staging")
APPROVED_DIR = Path("knowledge/approved")


class StagingQuarantineError(Exception):
    """Raised when quarantine constraints are violated."""
    pass


def audit_quarantine(
    staging_path: Path = STAGING_DIR,
    approved_path: Path = APPROVED_DIR
) -> Tuple[bool, List[str]]:
    """Audit staging and approved directories for quarantine breaches.
    
    Returns:
        (is_clean, issues_list)
    """
    issues = []
    
    # 1. Check approved directory: must contain ONLY approved records
    if approved_path.exists():
        for file_path in approved_path.rglob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                fm_data, _, err = extract_frontmatter(content)
                if err or not fm_data:
                    issues.append(f"UNPARSEABLE RECORD in approved path: {file_path} ({err})")
                    continue
                status = fm_data.get("approval_status")
                if status != ApprovalStatus.APPROVED.value and status != ApprovalStatus.APPROVED:
                    issues.append(
                        f"CRITICAL LEAK: Non-approved record found in approved path: {file_path} (status={status})"
                    )
                # Verify schema validity
                val_result = validate_markdown_file(file_path)
                if not val_result.is_valid:
                    issues.append(f"INVALID RECORD in approved path: {file_path} errors: {val_result.errors}")
            except Exception as e:
                issues.append(f"CORRUPT FILE in approved path: {file_path} ({e})")
                
    # 2. Check staging directory: should NOT contain approved records (they must be promoted and moved)
    if staging_path.exists():
        for file_path in staging_path.rglob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                fm_data, _, err = extract_frontmatter(content)
                if err or not fm_data:
                    issues.append(f"STAGING ERROR: Unparseable file in staging: {file_path} ({err})")
                    continue
                status = fm_data.get("approval_status")
                if status == ApprovalStatus.APPROVED.value or status == ApprovalStatus.APPROVED:
                    issues.append(
                        f"STAGING WARNING: Record marked 'approved' still in staging: {file_path}. Needs migration."
                    )
            except Exception as e:
                issues.append(f"STAGING ERROR: Unparseable file in staging: {file_path} ({e})")

    is_clean = len(issues) == 0
    return is_clean, issues


def promote_to_approved(
    staging_file: Path,
    approver: str,
    approved_dir: Path = APPROVED_DIR,
    effective_academic_year: Optional[str] = None
) -> Path:
    """Promote a staging Markdown file to approved status and move it to knowledge/approved/.
    
    Args:
        staging_file: Path to Markdown file in staging.
        approver: Email or ID of designated college administrator.
        approved_dir: Target approved base directory.
        effective_academic_year: Academic year (optional override).
        
    Returns:
        Path to promoted file in approved directory.
    """
    if not staging_file.exists():
        raise FileNotFoundError(f"Staging file not found: {staging_file}")
        
    content = staging_file.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise StagingQuarantineError("File lacks valid YAML frontmatter delimiters '---'")
        
    raw_yaml = parts[1]
    body = parts[2]
    data = yaml.safe_load(raw_yaml) or {}
    
    # Update governance metadata
    data["approval_status"] = ApprovalStatus.APPROVED.value
    data["approved_by"] = approver
    data["approval_date"] = date.today().isoformat()
    data["last_verified_date"] = date.today().isoformat()
    if effective_academic_year:
        data["effective_academic_year"] = effective_academic_year
        
    # Validate against strict Pydantic schema before committing
    try:
        validated = DocumentFrontmatter(**data)
    except Exception as e:
        raise StagingQuarantineError(f"Validation failed during promotion: {e}")
        
    # Prepare target path: knowledge/approved/<category>/<filename>
    category = validated.category.value
    target_category_dir = approved_dir / category
    target_category_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_category_dir / staging_file.name
    
    # Reassemble file with clean YAML
    new_yaml = yaml.dump(data, sort_keys=False, default_flow_style=False)
    new_content = f"---\n{new_yaml}---\n{body.lstrip()}"
    
    # Write to target
    target_path.write_text(new_content, encoding="utf-8")
    
    # Verify the newly written target file passes validator
    val_result = validate_markdown_file(target_path)
    if not val_result.is_valid:
        if target_path.exists():
            target_path.unlink()
        raise StagingQuarantineError(f"Promoted file failed post-write verification: {val_result.errors}")
        
    # Remove from staging
    staging_file.unlink()
    
    return target_path


def main():
    parser = argparse.ArgumentParser(description="Staging Quarantine & Promotion CLI")
    parser.add_argument("--audit", action="store_true", help="Audit staging and approved directories")
    parser.add_argument("--promote", type=str, help="Path to staging file to promote")
    parser.add_argument("--approver", type=str, help="Designated administrator email for promotion")
    parser.add_argument("--academic-year", type=str, default="2026-2027", help="Academic year (default: 2026-2027)")
    
    args = parser.parse_args()
    
    if args.audit:
        clean, issues = audit_quarantine()
        if clean:
            print("[PASS] Quarantine audit clean. Zero leaks detected.")
            sys.exit(0)
        else:
            print("[FAIL] Quarantine audit detected issues:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
            
    if args.promote:
        if not args.approver:
            print("Error: --approver is required when promoting a document.")
            sys.exit(1)
        try:
            target = promote_to_approved(
                Path(args.promote),
                approver=args.approver,
                effective_academic_year=args.academic_year
            )
            print(f"[SUCCESS] Document promoted and moved to: {target}")
            sys.exit(0)
        except Exception as e:
            print(f"[ERROR] Promotion failed: {e}")
            sys.exit(1)
            
    parser.print_help()


if __name__ == "__main__":
    main()
