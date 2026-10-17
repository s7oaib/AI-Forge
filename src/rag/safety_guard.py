"""Retrieval-side query hygiene and safety classification (SEC-01).

- normalize_query: strips stopwords for BM25/dense queries (avoids OR-join
  noise from filler words).
- classify_request: catches prohibited scopes (personal records, PII
  harvesting, credential/credential-like requests) and returns a category.
"""

from __future__ import annotations

import re

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "being", "been",
    "do", "does", "did", "have", "has", "had", "can", "could", "i", "me",
    "my", "we", "you", "your", "they", "them", "it", "its", "this", "that",
    "what", "when", "where", "who", "whom", "which", "how", "why", "of",
    "for", "in", "on", "at", "to", "from", "by", "with", "about", "and",
    "or", "if", "there", "their", "so", "as", "any", "all", "will", "shall",
    "please", "tell", "give", "some", "info", "information", "ask",
}

_REFUSAL_BY_CATEGORY = {
    "personal_contact":
        "I'm unable to provide personal contact details or private information "
        "about individuals. Public contact details are on the official website.",
    "personal_record":
        "I'm sorry, but the chatbot cannot access or disclose personal student "
        "records. Please contact the registrar's office.",
    "credential":
        "I can't provide passwords, credentials, or account details through "
        "this assistant.",
}

_PII_REQUEST_RE = re.compile(
    r"(personal\s+(?:phone|mobile|number|email|address|details?|records?)|"
    r"home\s+address|salary\s+of\s+|phone\s+number\s+of|"
    r"(?:social|security)\s+number)",
    re.I,
)
_CREDENTIAL_RE = re.compile(r"\b(password|passwd|credentials?|login\s+id)\b", re.I)
_RECORD_RE = re.compile(
    r"\b(fee\s+receipt|grade\s+report|marksheet|transcript|adhaar|aadhaar)\b",
    re.I,
)


def normalize_query(text: str) -> str:
    return " ".join(t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS).strip()


def sanitize_for_retrieval(text: str) -> str:
    """Defang prompt-injection payloads: strip obvious instruction fragments
    before the query string is used for BM25/dense search."""
    return re.sub(r"ignore[^\n.]{0,80}(instructions?|rules?)", " ", text, flags=re.I)


def classify_request(question: str) -> str | None:
    if _PII_REQUEST_RE.search(question):
        return "personal_contact"
    if _RECORD_RE.search(question):
        return "personal_record"
    if _CREDENTIAL_RE.search(question):
        return "credential"
    return None


def refusal(category: str) -> str | None:
    return _REFUSAL_BY_CATEGORY.get(category)
