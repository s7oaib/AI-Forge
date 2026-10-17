"""Governance and Markdown frontmatter validation for College Information Chatbot."""

import os
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
from pydantic import ValidationError

from src.core.schema import DocumentFrontmatter, ApprovalStatus


class ValidationResult:
    def __init__(self, file_path: str, is_valid: bool, frontmatter: Optional[DocumentFrontmatter] = None, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        self.file_path = file_path
        self.is_valid = is_valid
        self.frontmatter = frontmatter
        self.errors = errors or []
        self.warnings = warnings or []

    def __repr__(self):
        return f"<ValidationResult file={self.file_path} valid={self.is_valid} errors={len(self.errors)} warnings={len(self.warnings)}>"


def extract_frontmatter(content: str) -> Tuple[Optional[Dict], str, Optional[str]]:
    """
    Extracts YAML frontmatter and body from Markdown text.
    Returns: (frontmatter_dict, body_text, error_message)
    """
    if not content.startswith("---"):
        return None, content, "File does not start with YAML frontmatter delimiter '---'"
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content, "Incomplete YAML frontmatter: missing closing delimiter '---'"
    
    raw_yaml = parts[1]
    body = parts[2].strip()
    
    try:
        data = yaml.safe_load(raw_yaml)
        if not isinstance(data, dict):
            return None, body, "YAML frontmatter must be a key-value mapping"
        return data, body, None
    except yaml.YAMLError as e:
        return None, body, f"YAML parsing error: {e}"


def validate_markdown_file(file_path: str, reference_date: Optional[date] = None) -> ValidationResult:
    """
    Validates a single Markdown document against the authoritative schema and governance rules.
    """
    path = Path(file_path)
    if not path.is_file():
        return ValidationResult(str(path), False, errors=[f"File not found: {file_path}"])
    
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return ValidationResult(str(path), False, errors=[f"Cannot read file: {e}"])
    
    data, body, extract_err = extract_frontmatter(content)
    if extract_err:
        return ValidationResult(str(path), False, errors=[extract_err])
    
    ref_date = reference_date or date.today()
    errors = []
    warnings = []
    
    # 1. Validate Pydantic Schema
    try:
        model = DocumentFrontmatter(**data)
    except ValidationError as e:
        for err in e.errors():
            loc = " -> ".join(str(l) for l in err["loc"])
            errors.append(f"Schema error at [{loc}]: {err['msg']}")
        return ValidationResult(str(path), False, errors=errors)
    
    # 2. Institutional Governance Rules
    if model.approval_status != ApprovalStatus.APPROVED:
        warnings.append(f"Document approval_status is '{model.approval_status.value}' (not approved for active query index)")
    
    if model.review_before_date and model.review_before_date < ref_date:
        warnings.append(f"Document has expired (review_before_date: {model.review_before_date} < reference_date: {ref_date})")
    
    if not body:
        warnings.append("Document markdown body is empty")
        
    return ValidationResult(str(path), True, frontmatter=model, errors=errors, warnings=warnings)


def validate_directory(dir_path: str, reference_date: Optional[date] = None) -> Dict[str, ValidationResult]:
    """
    Scans a directory recursively and validates all .md files.
    """
    results = {}
    p = Path(dir_path)
    if not p.exists():
        return results
    
    for f in p.glob("**/*.md"):
        results[str(f)] = validate_markdown_file(str(f), reference_date)
        
    return results


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "knowledge/approved"
    print(f"Validating Markdown files in: {target}")
    res = validate_directory(target)
    failed = False
    for path, r in res.items():
        status = "PASS" if r.is_valid and not r.errors else "FAIL"
        print(f"[{status}] {path}")
        for e in r.errors:
            print(f"  ERROR: {e}")
            failed = True
        for w in r.warnings:
            print(f"  WARN:  {w}")
    if failed:
        sys.exit(1)
    print("All scanned files are structurally valid.")
