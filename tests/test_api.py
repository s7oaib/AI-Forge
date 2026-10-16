"""The web layer, plus the six live-demo questions end to end."""

import pytest


def test_index_page_loads(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"College Information Assistant" in res.data


def test_static_assets_load(client):
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200


def test_status_reports_offline_mode_and_files(client):
    data = client.get("/api/status").get_json()
    assert data["mode"] == "offline" and data["passages"] > 0 and len(data["files"]) == 5


def test_chat_returns_answer_with_sources(client):
    data = client.post("/api/chat", json={"message": "How do I apply for admission?"}).get_json()
    assert data["grounded"] and data["sources"][0]["file"] == "admissions.md"
    assert data["trace"]["candidates"][0]["passed"]


def test_knowledge_endpoint_lists_files_and_sections(client):
    data = client.get("/api/knowledge").get_json()
    assert len(data["files"]) == 5 and data["warnings"] == []
    assert all(f["sections"] for f in data["files"])


@pytest.mark.parametrize("payload", [{"message": ""}, {"message": "   "}, {}, {"message": None}])
def test_empty_message_is_a_400_with_readable_error(client, payload):
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 400 and "question" in res.get_json()["error"]


def test_non_json_body_is_a_400(client):
    res = client.post("/api/chat", data="hello", content_type="text/plain")
    assert res.status_code == 400 and "JSON" in res.get_json()["error"]


def test_unknown_route_is_json_404(client):
    res = client.get("/api/nope")
    assert res.status_code == 404 and "error" in res.get_json()


DEMO = [
    ("What departments are available?", True, "departments.md"),
    ("Which academic programs can I choose from?", True, "departments.md"),
    ("What facilities does the college have?", True, "facilities.md"),
    ("How do I apply for admission?", True, "admissions.md"),
    ("What are the office hours?", True, "college_overview.md"),
    ("What was the college's placement percentage last year?", False, "faq.md"),
]


@pytest.mark.parametrize("question, grounded, source", DEMO)
def test_live_demo_script(client, question, grounded, source):
    data = client.post("/api/chat", json={"message": question}).get_json()
    assert data["grounded"] is grounded
    assert data["sources"][0]["file"] == source
