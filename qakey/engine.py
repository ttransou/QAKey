"""Lightweight NLP matching engine for QAKey.

Pipeline per query
------------------
1. Normalize  – lowercase, remove punctuation
2. Tokenize   – split on whitespace
3. Stopwords  – remove common English function words
4. Stem       – simple suffix-stripping
5. Synonyms   – expand tokens using the synonyms dictionary
6. TF-IDF     – build weighted vectors for query and each document
7. Cosine sim – score each active record
8. Threshold  – return the best match if confidence ≥ threshold
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .models import QARecord

# ---------------------------------------------------------------------------
# Stop-words
# ---------------------------------------------------------------------------

STOPWORDS: frozenset = frozenset(
    {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "up", "about", "into",
        "through", "during", "before", "after", "above", "below", "between",
        "each", "own", "so", "than", "too", "very", "just", "or", "and",
        "but", "if", "as", "i", "me", "my", "we", "our", "you", "your",
        "he", "she", "it", "they", "them", "his", "her", "its", "their",
        "what", "which", "who", "when", "where", "why", "how", "s", "t",
        "this", "that", "these", "those", "also", "not", "no", "nor",
    }
)

# ---------------------------------------------------------------------------
# Text processing helpers
# ---------------------------------------------------------------------------

_CONTRACTION_MAP = {
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "won't": "will not",
    "can't": "cannot",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "i'm": "i am",
    "i've": "i have",
    "i'll": "i will",
    "i'd": "i would",
    "it's": "it is",
    "they're": "they are",
    "we're": "we are",
    "you're": "you are",
    "he's": "he is",
    "she's": "she is",
    "that's": "that is",
    "there's": "there is",
    "what's": "what is",
    "how's": "how is",
}

_SUFFIX_STRIP = [
    "ation", "ations", "ingly", "ness", "ment", "able", "ible",
    "ful", "less", "ous", "ive", "ize", "ise", "ing", "tion",
    "ed", "er", "ly", "es", "s",
]


def _expand_contractions(text: str) -> str:
    for contraction, expansion in _CONTRACTION_MAP.items():
        text = text.replace(contraction, expansion)
    return text


def normalize(text: str) -> str:
    """Lowercase, expand contractions, remove punctuation."""
    text = text.lower()
    text = _expand_contractions(text)
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> List[str]:
    return [t for t in text.split() if t]


def remove_stopwords(tokens: List[str]) -> List[str]:
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def stem(word: str) -> str:
    """Simple suffix-stripping stemmer (no external dependencies)."""
    for suffix in _SUFFIX_STRIP:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def process(text: str, synonyms: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """Full text processing pipeline → list of stemmed, expanded tokens."""
    tokens = remove_stopwords(tokenize(normalize(text)))
    stemmed = [stem(t) for t in tokens]

    if synonyms:
        expanded: List[str] = []
        for token in stemmed:
            expanded.append(token)
            canonical = stem(token)
            if canonical in synonyms:
                expanded.extend(stem(s) for s in synonyms[canonical])
        stemmed = expanded

    return stemmed


# ---------------------------------------------------------------------------
# TF-IDF index
# ---------------------------------------------------------------------------

def _build_index(
    records: List[QARecord],
    synonyms: Optional[Dict[str, List[str]]] = None,
) -> Dict:
    """Return a dict with 'documents' (id→tokens) and 'idf' (term→weight)."""
    documents: Dict[str, List[str]] = {}

    for record in records:
        if record.status != "Active":
            continue
        combined = " ".join(
            [record.canonical_question] + list(record.alternate_phrasings)
        )
        documents[record.id] = process(combined, synonyms)

    n = len(documents)
    df: Dict[str, int] = {}
    for tokens in documents.values():
        for term in set(tokens):
            df[term] = df.get(term, 0) + 1

    idf: Dict[str, float] = {
        term: math.log((n + 1) / (freq + 1)) + 1.0
        for term, freq in df.items()
    }

    return {"documents": documents, "idf": idf}


def _cosine(
    query_tokens: List[str],
    doc_tokens: List[str],
    idf: Dict[str, float],
) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0

    def tf(tokens: List[str]) -> Dict[str, int]:
        freq: Dict[str, int] = {}
        for t in tokens:
            freq[t] = freq.get(t, 0) + 1
        return freq

    q_tf = tf(query_tokens)
    d_tf = tf(doc_tokens)
    all_terms = set(q_tf) | set(d_tf)

    dot = 0.0
    q_sq = 0.0
    d_sq = 0.0

    for term in all_terms:
        w = idf.get(term, 1.0)
        qv = q_tf.get(term, 0) * w
        dv = d_tf.get(term, 0) * w
        dot += qv * dv
        q_sq += qv ** 2
        d_sq += dv ** 2

    if q_sq == 0 or d_sq == 0:
        return 0.0

    return dot / (math.sqrt(q_sq) * math.sqrt(d_sq))


# ---------------------------------------------------------------------------
# Match result
# ---------------------------------------------------------------------------

@dataclass
class MatchResult:
    record: Optional[QARecord]
    confidence: float

    def to_dict(self) -> dict:
        if self.record is None:
            return {
                "matched": False,
                "confidence": round(self.confidence, 4),
                "answer": None,
                "canonical_question": None,
                "record_id": None,
            }
        return {
            "matched": True,
            "confidence": round(self.confidence, 4),
            "answer": self.record.answer,
            "canonical_question": self.record.canonical_question,
            "record_id": self.record.id,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class QAEngine:
    """Question-matching engine with TF-IDF cosine similarity."""

    def __init__(
        self,
        records: List[QARecord],
        synonyms: Optional[Dict[str, List[str]]] = None,
        confidence_threshold: float = 0.25,
    ) -> None:
        self.synonyms = synonyms or {}
        self.confidence_threshold = confidence_threshold
        self._records_by_id: Dict[str, QARecord] = {r.id: r for r in records}
        self._index = _build_index(records, self.synonyms)

    def rebuild(self, records: List[QARecord]) -> None:
        """Rebuild the index after content changes."""
        self._records_by_id = {r.id: r for r in records}
        self._index = _build_index(records, self.synonyms)

    def match(self, query: str) -> MatchResult:
        """Match *query* to the best active Q&A record."""
        if not query.strip():
            return MatchResult(record=None, confidence=0.0)

        q_tokens = process(query, self.synonyms)
        if not q_tokens:
            return MatchResult(record=None, confidence=0.0)

        idf = self._index["idf"]
        documents = self._index["documents"]

        best_score = 0.0
        best_id: Optional[str] = None

        for record_id, doc_tokens in documents.items():
            score = _cosine(q_tokens, doc_tokens, idf)
            if score > best_score:
                best_score = score
                best_id = record_id

        if best_id and best_score >= self.confidence_threshold:
            return MatchResult(
                record=self._records_by_id.get(best_id),
                confidence=best_score,
            )

        return MatchResult(record=None, confidence=best_score)
