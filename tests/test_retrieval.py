"""Requirements 2 (known fact), 3 (rephrased question) and 5 (source file)."""

import pytest

from chatbot.knowledge import load_knowledge
from chatbot.retrieval import Retriever, is_follow_up, stem, tokenize
from tests.conftest import REAL_KNOWLEDGE


@pytest.fixture(scope="module")
def retriever():
    return Retriever(load_knowledge(REAL_KNOWLEDGE).chunks)


def top(retriever, question, context=None):
    results = retriever.search(question, context=context)
    assert results, f"no evidence found for {question!r}"
    return results[0].chunk


@pytest.mark.parametrize("question, source, heading", [
    ("What departments are available?", "departments.md", "Departments Available"),
    ("What facilities does the college have?", "facilities.md", "Facilities Overview"),
    ("How do I apply for admission?", "admissions.md", "How to Apply for Admission"),
    ("What are the office hours?", "college_overview.md", "Office Hours"),
    ("When is the library open?", "facilities.md", "Library Hours"),
    ("How can I contact the college?", "faq.md", "How do I contact the college?"),
])
def test_known_fact_and_its_source(retriever, question, source, heading):
    chunk = top(retriever, question)
    assert (chunk.source, chunk.heading) == (source, heading)


@pytest.mark.parametrize("rephrased", [
    "Which academic programs can I choose from?",
    "What courses do you offer?",
    "Which departments does the college have?",
    "what DEPARTMENTS are there",
])
def test_rephrased_questions_find_the_same_fact(retriever, rephrased):
    assert top(retriever, rephrased).heading == "Departments Available"


@pytest.mark.parametrize("rephrased", ["What are the timings of the office?", "When is the office open?"])
def test_rephrased_office_hours(retriever, rephrased):
    assert top(retriever, rephrased).heading == "Office Hours"


@pytest.mark.parametrize("question", [
    "What was the college's placement percentage last year?",
    "Who is the principal?",
    "Do you have a swimming pool?",
    "What is the capital of France?",
])
def test_unsupported_questions_return_no_evidence(retriever, question):
    assert retriever.search(question) == []


def test_follow_up_uses_previous_question(retriever):
    assert is_follow_up("What about Saturday?")
    assert top(retriever, "What about Saturday?", context="What are the office hours?").heading == "Office Hours"


def test_follow_up_context_cannot_smuggle_in_an_answer(retriever):
    # The previous question matches office hours, but the new one asks about something unknown.
    assert retriever.search("And what is its placement record?", context="What are the office hours?") == []


def test_tokenizer_normalises_words():
    assert stem("facilities") == "facility" and stem("timings") == stem("timing")
    assert tokenize("What are the Office HOURS?") == ["office", "hour"]


def test_empty_knowledge_base_returns_nothing():
    assert Retriever([]).search("What departments are available?") == []
