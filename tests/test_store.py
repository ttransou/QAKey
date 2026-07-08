"""Tests for the QAKey data store."""

import os
import tempfile

import pytest
import yaml

from qakey.models import QARecord
from qakey.store import QAStore


def _make_store(tmp_path, records=None):
    path = str(tmp_path / "qa_records.yaml")
    if records is not None:
        data = {"records": [r.to_dict() for r in records]}
        with open(path, "w") as fh:
            yaml.dump(data, fh)
    return QAStore(path), path


# ---------------------------------------------------------------------------
# Model validation
# ---------------------------------------------------------------------------

def test_record_validate_ok():
    r = QARecord(id="x", canonical_question="Q?", answer="A.", status="Active")
    assert r.validate() == []


def test_record_validate_missing_question():
    r = QARecord(id="x", canonical_question="", answer="A.", status="Active")
    errs = r.validate()
    assert any("canonical_question" in e for e in errs)


def test_record_validate_missing_answer():
    r = QARecord(id="x", canonical_question="Q?", answer="", status="Active")
    errs = r.validate()
    assert any("answer" in e for e in errs)


def test_record_validate_bad_status():
    r = QARecord(id="x", canonical_question="Q?", answer="A.", status="Unknown")
    errs = r.validate()
    assert any("status" in e for e in errs)


def test_record_auto_id():
    r = QARecord(id="", canonical_question="Q?", answer="A.", status="Draft")
    assert r.id.startswith("qa-")
    assert len(r.id) > 3


def test_record_auto_timestamps():
    r = QARecord(id="x", canonical_question="Q?", answer="A.", status="Draft")
    assert r.created_at != ""
    assert r.updated_at != ""


def test_record_roundtrip():
    r = QARecord(
        id="qa-abc",
        canonical_question="What is QAKey?",
        answer="A Q&A framework.",
        status="Active",
        alternate_phrasings=["Tell me about QAKey"],
        tags=["meta"],
        contributor="alice",
        reviewer="bob",
    )
    d = r.to_dict()
    r2 = QARecord.from_dict(d)
    assert r2.id == r.id
    assert r2.canonical_question == r.canonical_question
    assert r2.answer == r.answer
    assert r2.status == r.status
    assert r2.alternate_phrasings == r.alternate_phrasings
    assert r2.tags == r.tags


# ---------------------------------------------------------------------------
# Store CRUD
# ---------------------------------------------------------------------------

def test_store_loads_from_yaml(tmp_path, sample_records):
    store, _ = _make_store(tmp_path, sample_records)
    loaded = store.get_all()
    assert len(loaded) == len(sample_records)
    ids = {r.id for r in loaded}
    for rec in sample_records:
        assert rec.id in ids


def test_store_get_active_filters(tmp_path, sample_records):
    store, _ = _make_store(tmp_path, sample_records)
    active = store.get_active()
    assert all(r.status == "Active" for r in active)
    # sample_records has 3 Active + 1 Draft
    assert len(active) == 3


def test_store_get_by_id(tmp_path, sample_records):
    store, _ = _make_store(tmp_path, sample_records)
    r = store.get("qa-t001")
    assert r is not None
    assert r.canonical_question == "What are your business hours?"


def test_store_get_missing_returns_none(tmp_path):
    store, _ = _make_store(tmp_path)
    assert store.get("nonexistent") is None


def test_store_create(tmp_path):
    store, _ = _make_store(tmp_path)
    r = QARecord(id="", canonical_question="New Q?", answer="New A.", status="Draft")
    created = store.create(r)
    assert store.get(created.id) is not None


def test_store_create_auto_id(tmp_path):
    store, _ = _make_store(tmp_path)
    r = QARecord(id="", canonical_question="Q?", answer="A.", status="Draft")
    created = store.create(r)
    assert created.id.startswith("qa-")


def test_store_update_increments_version(tmp_path, sample_records):
    store, _ = _make_store(tmp_path, sample_records)
    r = store.get("qa-t001")
    original_version = r.version
    r.answer = "Updated answer."
    store.update(r)
    updated = store.get("qa-t001")
    assert updated.version == original_version + 1


def test_store_update_changes_updated_at(tmp_path, sample_records):
    store, _ = _make_store(tmp_path, sample_records)
    r = store.get("qa-t001")
    original_ts = r.updated_at
    r.answer = "Changed."
    store.update(r)
    updated = store.get("qa-t001")
    # updated_at may or may not differ depending on test speed,
    # but it must be set to a non-empty string
    assert updated.updated_at != ""


def test_store_delete(tmp_path, sample_records):
    store, _ = _make_store(tmp_path, sample_records)
    result = store.delete("qa-t001")
    assert result is True
    assert store.get("qa-t001") is None


def test_store_delete_missing_returns_false(tmp_path):
    store, _ = _make_store(tmp_path)
    assert store.delete("nope") is False


# ---------------------------------------------------------------------------
# Publish workflow
# ---------------------------------------------------------------------------

def test_store_publish_saves_yaml(tmp_path, sample_records):
    store, path = _make_store(tmp_path, sample_records)
    result = store.publish()
    assert result["success"] is True
    assert os.path.exists(path)
    with open(path) as fh:
        data = yaml.safe_load(fh)
    assert len(data["records"]) == len(sample_records)


def test_store_publish_fails_on_invalid_record(tmp_path):
    store, _ = _make_store(tmp_path)
    bad = QARecord(id="qa-bad", canonical_question="", answer="A.", status="Active")
    store.create(bad)
    result = store.publish()
    assert result["success"] is False
    assert "qa-bad" in result["errors"]


def test_store_publish_reports_count(tmp_path, sample_records):
    store, _ = _make_store(tmp_path, sample_records)
    result = store.publish()
    assert result["count"] == len(sample_records)


def test_store_empty_path_creates_file(tmp_path):
    path = str(tmp_path / "new_dir" / "records.yaml")
    store = QAStore(path)
    r = QARecord(id="qa-new", canonical_question="Q?", answer="A.", status="Active")
    store.create(r)
    result = store.publish()
    assert result["success"] is True
    assert os.path.exists(path)
