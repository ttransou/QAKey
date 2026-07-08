"""Tests for the QAKey matching engine."""

import pytest

from qakey.engine import (
    QAEngine,
    MatchResult,
    normalize,
    process,
    stem,
    remove_stopwords,
    tokenize,
    _cosine,
)
from qakey.models import QARecord


# ---------------------------------------------------------------------------
# Unit tests — text processing helpers
# ---------------------------------------------------------------------------

def test_normalize_lowercases():
    assert normalize("HELLO World!") == "hello world"


def test_normalize_removes_punctuation():
    # Contractions are expanded before punctuation is stripped
    assert normalize("What's the policy?") == "what is the policy"


def test_normalize_collapses_whitespace():
    assert normalize("too   many   spaces") == "too many spaces"


def test_normalize_expands_contraction():
    assert "do not" in normalize("don't do it")


def test_tokenize_basic():
    assert tokenize("hello world") == ["hello", "world"]


def test_remove_stopwords():
    tokens = ["what", "is", "the", "policy", "for", "employees"]
    result = remove_stopwords(tokens)
    # "what", "is", "the", "for" should be removed
    assert "policy" in result
    assert "employees" in result
    assert "the" not in result
    assert "is" not in result


def test_stem_removes_ing():
    assert stem("working") == "work"


def test_stem_removes_ed():
    assert stem("worked") == "work"


def test_stem_removes_tion():
    # "connection" ends in "tion" (not "ation"), so suffix "tion" is stripped
    assert stem("connection") == "connec"


def test_stem_short_word_unchanged():
    # Stemmer should not strip suffix from very short words
    assert stem("run") == "run"


def test_process_returns_list_of_strings():
    tokens = process("What are the business hours?")
    assert isinstance(tokens, list)
    assert all(isinstance(t, str) for t in tokens)
    assert len(tokens) > 0


def test_process_synonym_expansion():
    synonyms = {"hour": ["schedule", "timing"]}
    tokens = process("hours", synonyms)
    # "hour" stem should be expanded
    assert any("schedul" in t or "schedule" in t or "tim" in t for t in tokens)


def test_cosine_identical_tokens():
    idf = {"hello": 1.0, "world": 1.0}
    score = _cosine(["hello", "world"], ["hello", "world"], idf)
    assert abs(score - 1.0) < 1e-9


def test_cosine_no_overlap():
    idf = {"hello": 1.0, "world": 1.0, "foo": 1.0, "bar": 1.0}
    score = _cosine(["hello", "world"], ["foo", "bar"], idf)
    assert score == 0.0


def test_cosine_empty_query():
    idf = {"hello": 1.0}
    assert _cosine([], ["hello"], idf) == 0.0


# ---------------------------------------------------------------------------
# Integration tests — QAEngine
# ---------------------------------------------------------------------------

def test_engine_matches_exact_canonical(sample_records):
    engine = QAEngine(sample_records)
    result = engine.match("What are your business hours?")
    assert result.record is not None
    assert result.record.id == "qa-t001"
    assert result.confidence > 0.5


def test_engine_matches_alternate_phrasing(sample_records):
    engine = QAEngine(sample_records)
    result = engine.match("When are you open?")
    assert result.record is not None
    assert result.record.id == "qa-t001"


def test_engine_matches_informal_phrasing(sample_records):
    engine = QAEngine(sample_records)
    result = engine.match("I forgot my password, how do I get back in?")
    assert result.record is not None
    assert result.record.id == "qa-t002"


def test_engine_matches_vacation_query(sample_records):
    engine = QAEngine(sample_records)
    result = engine.match("How many PTO days do I get per year?")
    assert result.record is not None
    assert result.record.id == "qa-t003"


def test_engine_no_match_for_nonsense(sample_records):
    engine = QAEngine(sample_records, confidence_threshold=0.25)
    result = engine.match("zzxzxzxzqqqq totally unrelated gibberish xyz")
    assert result.record is None


def test_engine_empty_query_returns_no_match(sample_records):
    engine = QAEngine(sample_records)
    result = engine.match("")
    assert result.record is None
    assert result.confidence == 0.0


def test_engine_whitespace_only_query(sample_records):
    engine = QAEngine(sample_records)
    result = engine.match("   ")
    assert result.record is None


def test_engine_skips_draft_records(sample_records):
    # "Draft: upcoming pet policy" is Draft status
    engine = QAEngine(sample_records)
    result = engine.match("pet policy")
    # Should not return the Draft record
    if result.record is not None:
        assert result.record.status == "Active"


def test_engine_rebuild_picks_up_new_record(sample_records):
    engine = QAEngine(sample_records)
    new_records = sample_records + [
        QARecord(
            id="qa-t005",
            canonical_question="Where is the cafeteria located?",
            alternate_phrasings=["Where can I eat lunch?", "Cafeteria location"],
            answer="The cafeteria is on the ground floor, east wing.",
            status="Active",
        )
    ]
    engine.rebuild(new_records)
    # Use a query that uniquely contains "cafeteria" to target the new record
    result = engine.match("cafeteria location")
    assert result.record is not None
    assert result.record.id == "qa-t005"


def test_match_result_to_dict_matched(sample_records):
    engine = QAEngine(sample_records)
    result = engine.match("business hours")
    assert result.record is not None
    d = result.to_dict()
    assert d["matched"] is True
    assert "answer" in d
    assert "canonical_question" in d
    assert isinstance(d["confidence"], float)


def test_match_result_to_dict_no_match(sample_records):
    engine = QAEngine(sample_records, confidence_threshold=0.99)
    result = engine.match("zyxwvutsrqponmlkjihgfedcba")
    d = result.to_dict()
    assert d["matched"] is False
    assert d["answer"] is None


def test_engine_with_synonyms(sample_records):
    synonyms = {"vacation": ["pto", "leave", "holiday"]}
    engine = QAEngine(sample_records, synonyms=synonyms)
    result = engine.match("How many vacation days am I entitled to?")
    assert result.record is not None
    assert result.record.id == "qa-t003"
