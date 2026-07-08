"""Flask application entry-point for QAKey."""

from __future__ import annotations

import os

import yaml
from flask import Flask, jsonify, render_template, request

from qakey.engine import QAEngine
from qakey.models import QARecord
from qakey.store import QAStore

# ---------------------------------------------------------------------------
# Initialise
# ---------------------------------------------------------------------------

app = Flask(__name__)

_CONFIG_PATH = os.environ.get("QAKEY_CONFIG", "config.yaml")

with open(_CONFIG_PATH, encoding="utf-8") as _fh:
    _config: dict = yaml.safe_load(_fh)

_store = QAStore(_config["knowledge"]["records_path"])

_synonyms: dict = {}
_synonyms_path = _config["knowledge"].get("synonyms_path", "")
if _synonyms_path and os.path.exists(_synonyms_path):
    with open(_synonyms_path, encoding="utf-8") as _fh:
        _syn_data = yaml.safe_load(_fh) or {}
    _synonyms = _syn_data.get("synonyms", {})

_engine = QAEngine(
    records=_store.get_active(),
    synonyms=_synonyms,
    confidence_threshold=_config.get("matching", {}).get("confidence_threshold", 0.25),
)

# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html", config=_config)


@app.route("/editor")
def editor():
    return render_template("editor.html", config=_config)


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------


@app.route("/api/query", methods=["POST"])
def api_query():
    """Match a user question and return the canonical answer."""
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400

    result = _engine.match(question)
    return jsonify(result.to_dict())


@app.route("/api/records", methods=["GET"])
def api_list_records():
    return jsonify([r.to_dict() for r in _store.get_all()])


@app.route("/api/records", methods=["POST"])
def api_create_record():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "request body required"}), 400

    record = QARecord.from_dict(body)
    _store.create(record)
    return jsonify(record.to_dict()), 201


@app.route("/api/records/<record_id>", methods=["PUT"])
def api_update_record(record_id: str):
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "request body required"}), 400

    existing = _store.get(record_id)
    if existing is None:
        return jsonify({"error": "record not found"}), 404

    body["id"] = record_id
    body["created_at"] = existing.created_at
    record = QARecord.from_dict(body)
    _store.update(record)
    return jsonify(record.to_dict())


@app.route("/api/records/<record_id>", methods=["DELETE"])
def api_delete_record(record_id: str):
    if not _store.delete(record_id):
        return jsonify({"error": "record not found"}), 404
    return "", 204


@app.route("/api/publish", methods=["POST"])
def api_publish():
    """Validate all records, persist to YAML, and rebuild the index."""
    result = _store.publish()
    if result["success"]:
        _engine.rebuild(_store.get_active())
    return jsonify(result)


# ---------------------------------------------------------------------------
# Health-check
# ---------------------------------------------------------------------------


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "version": "1.0.0"})


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(
        debug=_config.get("debug", False),
        host=_config.get("host", "127.0.0.1"),
        port=_config.get("port", 5000),
    )
