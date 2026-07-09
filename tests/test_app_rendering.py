"""App-level tests for rendered answer payloads."""

import app as app_module
from app import app


def test_query_response_includes_rendered_answer_html():
    client = app.test_client()

    response = client.post(
        "/api/query",
        json={"question": "What are your business hours?"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["matched"] is True
    assert "answer_html" in payload
    assert payload["answer_html"]


def test_ingest_preview_includes_rendered_answer_html():
    client = app.test_client()

    response = client.post(
        "/api/ingest/preview",
        json={
            "text": "Question: What is included?\nAnswer:\n- Laptop\n- Training",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["records"]
    assert payload["records"][0]["answer_html"].startswith("<ul>")


def test_feedback_endpoint_creates_and_resolves_editor_alert(tmp_path, monkeypatch):
    feedback_path = tmp_path / "feedback" / "alerts.json"
    monkeypatch.setattr(
        app_module,
        "_fallback_cfg",
        {"enabled": True, "fallback_log_path": str(feedback_path), "max_alerts": 25},
    )

    client = app.test_client()
    response = client.post(
        "/api/feedback",
        json={
            "question": "What are your business hours?",
            "helpful": False,
            "matched": True,
            "record_id": "qa-t001",
            "fallback_type": None,
            "confidence": 0.98,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {"success": True, "recorded": True}

    alerts_response = client.get("/api/editor/feedback-alerts")
    assert alerts_response.status_code == 200
    alerts_payload = alerts_response.get_json()
    assert alerts_payload["count"] == 1

    alert = alerts_payload["alerts"][0]
    assert alert["question"] == "What are your business hours?"
    assert alert["record_id"] == "qa-t001"

    resolve_response = client.post(f"/api/editor/feedback-alerts/{alert['id']}/resolve")
    assert resolve_response.status_code == 200
    assert resolve_response.get_json() == {"success": True}

    final_alerts = client.get("/api/editor/feedback-alerts").get_json()
    assert final_alerts["count"] == 0