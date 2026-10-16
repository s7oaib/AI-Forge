"""Requirement 1 (loading) and 7 (malformed or missing files)."""

from chatbot.knowledge import load_knowledge, split_markdown
from tests.conftest import REAL_KNOWLEDGE


def test_loads_all_demo_files():
    kb = load_knowledge(REAL_KNOWLEDGE)
    assert kb.files == ["admissions.md", "college_overview.md", "departments.md", "facilities.md", "faq.md"]
    assert kb.warnings == []
    assert len(kb.chunks) >= 15
    headings = {c.heading for c in kb.chunks}
    assert {"Departments Available", "Office Hours", "How to Apply for Admission"} <= headings


def test_split_markdown_keeps_file_title_and_heading():
    chunks = split_markdown("x.md", "# Title\n\n> banner line\n\n## First\nAlpha\n\n## Second\nBeta\n")
    assert [(c.source, c.title, c.heading, c.text) for c in chunks] == [
        ("x.md", "Title", "First", "Alpha"),
        ("x.md", "Title", "Second", "Beta"),
    ]


def test_file_without_headings_still_loads(tmp_path):
    (tmp_path / "notes.md").write_text("Just a plain paragraph about the canteen.", encoding="utf-8")
    kb = load_knowledge(tmp_path)
    assert kb.files == ["notes.md"]
    assert kb.chunks[0].heading == "Notes"


def test_missing_folder_gives_warning_not_crash(tmp_path):
    kb = load_knowledge(tmp_path / "does-not-exist")
    assert kb.chunks == []
    assert any("not found" in w for w in kb.warnings)


def test_bad_files_are_skipped_and_good_ones_kept(tmp_path):
    (tmp_path / "good.md").write_text("# Good\n\n## Library\nOpen daily.", encoding="utf-8")
    (tmp_path / "empty.md").write_text("", encoding="utf-8")
    (tmp_path / "binary.md").write_bytes(b"\xff\xfe\x00\x81 not utf-8 \x9c")
    kb = load_knowledge(tmp_path)
    assert kb.files == ["good.md"]
    assert len(kb.warnings) == 2
    assert any("empty.md" in w for w in kb.warnings)
    assert any("binary.md" in w for w in kb.warnings)


def test_empty_folder_reports_no_usable_files(tmp_path):
    kb = load_knowledge(tmp_path)
    assert kb.files == [] and any("No usable" in w for w in kb.warnings)
