"""Keyword retrieval: find the knowledge passages that best match a question.

How it works, in plain terms:

1. Tokenize: lowercase the text, drop filler words ("what", "the", "is"),
   and reduce words to a simple base form ("facilities" -> "facility").
2. Expand synonyms: "programs", "courses" and "branches" also count as
   "department", so differently worded questions find the same passage.
3. Score every passage with BM25, the classic ranking formula used by search
   engines: rare words that appear in a passage count for more than common ones.
4. Check evidence: a passage only counts as support if it covers most of the
   meaningful words in the question. Unknown words like "placement" lower the
   coverage, which is how the bot knows to say "I don't have that information".

No embeddings, vector database or internet access are needed.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .knowledge import Chunk

# A passage must cover at least this share of the question's (weighted) words.
MIN_COVERAGE = 0.5
# Secondary passages must score at least this fraction of the best passage.
RELATIVE_SCORE_CUTOFF = 0.6
MAX_RESULTS = 3

STOPWORDS = set("""
a about above after again all also am an and any are as at be been before being
below between both but by can could did do does doing down during each else for
from further get got had has have having here how i if in into is it its itself
just let like may me might more most much must my myself need no nor not now of
off on once only or other our ours out over own please same shall she should so
some such than that the their them then there these they this those through to
too under until up us very want was we were what when where which while who whom
why will with would you your yours tell know give show find list explain describe
any anything something thing things kind type types sort available offer offered
""".split())

# Words that appear everywhere in a college knowledge base, so they say little
# about *which* fact is wanted. They are ignored for scoring and coverage.
GENERIC = {"college", "campus", "greenfield", "demo", "student", "institute",
           "institution", "university", "information", "info", "detail"}

# Each line: words a user might type -> base words used in the knowledge files.
# Add your own here to teach the bot new phrasings.
SYNONYMS = {
    "program": ["department", "program"], "programme": ["department", "program"],
    "course": ["department", "program"], "branch": ["department", "program"],
    "degree": ["department", "program"], "stream": ["department", "program"],
    "major": ["department", "program"], "specialization": ["department", "program"],
    "department": ["program"], "dept": ["department", "program"],
    "amenity": ["facility"], "infrastructure": ["facility"], "service": ["facility"],
    "apply": ["admission", "application"], "application": ["admission", "apply"],
    "enroll": ["admission", "apply"], "enrol": ["admission", "apply"],
    "join": ["admission", "apply"], "register": ["admission", "apply"],
    "registration": ["admission", "apply"], "admit": ["admission"],
    "admission": ["apply"], "intake": ["admit"],
    "hour": ["open"], "timing": ["hour", "open"], "time": ["hour", "open"],
    "schedule": ["hour", "open"], "working": ["open", "hour"], "open": ["hour"],
    "contact": ["email", "phone"], "reach": ["contact", "email", "phone"],
    "email": ["contact"], "phone": ["contact"], "call": ["phone", "contact"],
    "cost": ["fee"], "price": ["fee"], "tuition": ["fee"], "pay": ["fee"],
    "accommodation": ["hostel"], "dorm": ["hostel"], "dormitory": ["hostel"],
    "housing": ["hostel"], "stay": ["hostel"],
    "book": ["library"], "transportation": ["transport", "bus"],
    "commute": ["transport", "bus"], "bus": ["transport"],
    "eligible": ["eligibility"], "qualification": ["eligibility"],
    "requirement": ["eligibility"], "criteria": ["eligibility"],
    "game": ["sport"], "gym": ["sport"], "playground": ["sport"],
    "food": ["cafeteria"], "canteen": ["cafeteria"], "mess": ["cafeteria"],
    "lunch": ["cafeteria"], "eat": ["cafeteria"], "internet": ["wifi"],
    "lab": ["laboratory"], "laboratory": ["lab"],
    "semester": ["calendar"], "term": ["semester", "calendar"],
    "holiday": ["break", "closed"], "vacation": ["break"],
    "long": ["duration"], "duration": ["year"],
    "aid": ["scholarship"], "financial": ["scholarship"],
}

FOLLOW_UP_STARTS = ("what about", "how about", "and ", "also ", "what else", "tell me more", "more about")
FOLLOW_UP_PRONOUNS = {"it", "its", "they", "them", "their", "there", "that", "those", "these"}


def stem(word: str) -> str:
    """A deliberately tiny stemmer: enough to match plurals and -ing forms."""
    if len(word) > 4 and word.endswith(("ies", "ied")):
        word = word[:-3] + "y"
    elif len(word) > 4 and word.endswith(("sses", "shes", "ches", "xes")):
        word = word[:-2]
    elif len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        word = word[:-1]
    if len(word) > 5 and word.endswith("ing"):
        word = word[:-3]
    return word


# Store synonyms in stemmed form so they line up with tokenize().
SYNONYMS = {stem(k): sorted({stem(v) for v in vs}) for k, vs in SYNONYMS.items()}


def tokenize(text: str) -> list[str]:
    text = text.lower().replace("wi-fi", "wifi").replace("’", "'")
    words = re.findall(r"[a-z0-9]+", text)
    return [stem(w) for w in words if w not in STOPWORDS and len(w) > 1]


def keywords(question: str) -> list[tuple[str, list[str]]]:
    """Meaningful question words, each with its synonyms: [("program", ["department"]), ...]."""
    found, seen = [], set()
    for token in tokenize(question):
        if token in GENERIC or token in seen:
            continue
        seen.add(token)
        found.append((token, [s for s in SYNONYMS.get(token, []) if s != token]))
    return found


def query_groups(question: str) -> list[set[str]]:
    """Each meaningful question word becomes a group: {word, *its synonyms}."""
    return [{token, *syns} for token, syns in keywords(question)]


def ignored_words(question: str) -> list[str]:
    """Words dropped before searching (filler like "what", "the", or "college")."""
    words = re.findall(r"[a-z0-9]+", question.lower().replace("wi-fi", "wifi"))
    return [w for w in dict.fromkeys(words) if len(w) > 1 and (w in STOPWORDS or stem(w) in GENERIC)]


def is_follow_up(question: str) -> bool:
    q = question.lower().strip()
    if q.startswith(FOLLOW_UP_STARTS):
        return True
    words = set(re.findall(r"[a-z']+", q))
    return bool(words & FOLLOW_UP_PRONOUNS) or not query_groups(question)


@dataclass
class Result:
    chunk: Chunk
    score: float
    coverage: float


class Retriever:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        # The heading is repeated so that matching it counts a little extra.
        self.docs = [Counter(tokenize(f"{c.title} {c.heading} {c.heading} {c.text}")) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = (sum(self.lengths) / len(self.lengths)) if chunks else 0.0
        self.df: Counter = Counter()
        for d in self.docs:
            self.df.update(d.keys())

    def _idf(self, df: int) -> float:
        n = len(self.chunks)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def _group_idf(self, group: set[str]) -> float:
        # Unknown words get the highest weight, so they pull coverage down.
        df = sum(1 for d in self.docs if any(t in d for t in group))
        return self._idf(df)

    @staticmethod
    def _term_weights(text: str) -> dict[str, float]:
        """Words typed by the user weigh 1.0; their synonyms weigh 0.5."""
        weights: dict[str, float] = {}
        for token in tokenize(text):
            if token not in GENERIC:
                weights[token] = 1.0
                for syn in SYNONYMS.get(token, []):
                    weights.setdefault(syn, 0.5)
        return weights

    def _bm25(self, i: int, term_weights: dict[str, float]) -> float:
        doc, length, score = self.docs[i], self.lengths[i], 0.0
        for term, weight in term_weights.items():
            tf = doc.get(term, 0)
            if tf:
                norm = tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * length / self.avg_len))
                score += weight * self._idf(self.df[term]) * norm
        return score

    def _coverage(self, i: int, groups: list[set[str]], weights: list[float]) -> float:
        total = sum(weights)
        if not total:
            return 0.0
        hit = sum(w for g, w in zip(groups, weights) if any(t in self.docs[i] for t in g))
        return hit / total

    def score_all(self, question: str, context: str | None = None) -> list[Result]:
        """Score every passage that shares at least one word with the question, best first.

        `context` is the previous user question, used only for follow-ups such as
        "What about Saturday?". Evidence (coverage) is still checked against the
        *current* question whenever it has meaningful words of its own.
        """
        rank_text = f"{context} {question}" if context else question
        gate_groups = query_groups(question) or query_groups(rank_text)
        if not self.chunks or not gate_groups:
            return []

        term_weights = self._term_weights(rank_text)
        gate_weights = [self._group_idf(g) for g in gate_groups]
        results = []
        for i, chunk in enumerate(self.chunks):
            score = self._bm25(i, term_weights)
            if score > 0:
                coverage = self._coverage(i, gate_groups, gate_weights)
                results.append(Result(chunk, round(score, 3), round(coverage, 3)))
        results.sort(key=lambda r: (r.score, r.coverage), reverse=True)
        return results

    def search(self, question: str, context: str | None = None) -> list[Result]:
        """Return only passages that genuinely support the question, best first."""
        results = [r for r in self.score_all(question, context) if r.coverage >= MIN_COVERAGE]
        if not results:
            return []
        best = results[0].score
        return [r for r in results if r.score >= best * RELATIVE_SCORE_CUTOFF][:MAX_RESULTS]

    def candidates(self, question: str, context: str | None = None, limit: int = 4) -> list[Result]:
        """Top passages by score alone (no evidence check), for the LLM to judge."""
        return self.score_all(question, context)[:limit]
