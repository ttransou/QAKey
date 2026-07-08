"""End-to-end workflow tests for editor actions and user query behavior."""

from __future__ import annotations

import yaml

import app as app_module
from qakey.engine import QAEngine
from qakey.store import QAStore


def _seed_store_file(path: str) -> None:
    seed = {
        "records": [
            {
                "id": "qa-seed-001",
                "canonical_question": "What are your support hours?",
                "alternate_phrasings": ["When is support open?"],
                "answer": "Support is available Monday through Friday, 9 to 5.",
                "status": "Active",
                "tags": ["support"],
                "contributor": "seed",
                "reviewer": "seed",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "version": 1,
            }
        ]
    }
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(seed, fh, sort_keys=False)


def test_editor_lifecycle_controls_user_visible_behavior(tmp_path, monkeypatch):
    records_path = str(tmp_path / "qa_records.yaml")
    _seed_store_file(records_path)

    isolated_store = QAStore(records_path)
    isolated_engine = QAEngine(
        records=isolated_store.get_active(),
        synonyms={},
        confidence_threshold=0.15,
    )

    monkeypatch.setattr(app_module, "_store", isolated_store)
    monkeypatch.setattr(app_module, "_engine", isolated_engine)
    monkeypatch.setattr(app_module, "_editor_cfg", {"require_auth": False})

    client = app_module.app.test_client()

    create_payload = {
        "canonical_question": "How do I request a parking permit?",
        "alternate_phrasings": ["office parking pass", "parking permit request"],
        "answer": "Use the facilities request form.",
        "status": "Draft",
        "tags": ["facilities"],
        "contributor": "workflow-test",
        "reviewer": "ops",
    }

    create_response = client.post("/api/records", json=create_payload)
    assert create_response.status_code == 201
    created = create_response.get_json()
    record_id = created["id"]

    pre_publish_query = client.post(
        "/api/query",
        json={"question": "How do I get an office parking pass?"},
    ).get_json()
    assert pre_publish_query["matched"] is False

    created["status"] = "Active"
    created["answer"] = "Use the facilities request form and attach your vehicle details."
    activate_response = client.put(f"/api/records/{record_id}", json=created)
    assert activate_response.status_code == 200

    still_pre_publish_query = client.post(
        "/api/query",
        json={"question": "How do I get an office parking pass?"},
    ).get_json()
    assert still_pre_publish_query["matched"] is False

    publish_response = client.post("/api/publish")
    assert publish_response.status_code == 200
    assert publish_response.get_json()["success"] is True

    post_publish_query = client.post(
        "/api/query",
        json={"question": "How do I get an office parking pass?"},
    ).get_json()
    assert post_publish_query["matched"] is True
    assert post_publish_query["canonical_question"] == "How do I request a parking permit?"
    assert "vehicle details" in post_publish_query["answer"]

    updated = activate_response.get_json()
    updated["answer"] = "Use the facilities request form, attach your vehicle details, and wait for confirmation."
    refine_response = client.put(f"/api/records/{record_id}", json=updated)
    assert refine_response.status_code == 200

    client.post("/api/publish")
    refined_query = client.post(
        "/api/query",
        json={"question": "How do I get an office parking pass?"},
    ).get_json()
    assert "wait for confirmation" in refined_query["answer"]

    inactive = refine_response.get_json()
    inactive["status"] = "Inactive"
    deactivate_response = client.put(f"/api/records/{record_id}", json=inactive)
    assert deactivate_response.status_code == 200

    client.post("/api/publish")
    post_deactivate_query = client.post(
        "/api/query",
        json={"question": "How do I get an office parking pass?"},
    ).get_json()
    assert post_deactivate_query["matched"] is False
