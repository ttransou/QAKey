"""App-level tests for rendered answer payloads."""

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