"""YAML-backed data store for QAKey records."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import yaml

from .models import QARecord, _new_id, _utcnow


class QAStore:
    """Manages loading, persisting, and in-memory CRUD of QARecord objects."""

    def __init__(self, records_path: str) -> None:
        self.records_path = records_path
        self._records: Dict[str, QARecord] = {}
        self._load()

    # ------------------------------------------------------------------
    # Internal I/O
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not os.path.exists(self.records_path):
            return
        with open(self.records_path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        for record_data in data.get("records", []):
            record = QARecord.from_dict(record_data)
            self._records[record.id] = record

    def _save(self) -> None:
        data = {
            "records": [r.to_dict() for r in self._records.values()]
        }
        os.makedirs(os.path.dirname(self.records_path), exist_ok=True)
        with open(self.records_path, "w", encoding="utf-8") as fh:
            yaml.dump(
                data,
                fh,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def get_all(self) -> List[QARecord]:
        return list(self._records.values())

    def get_active(self) -> List[QARecord]:
        return [r for r in self._records.values() if r.status == "Active"]

    def get(self, record_id: str) -> Optional[QARecord]:
        return self._records.get(record_id)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, record: QARecord) -> QARecord:
        if not record.id:
            record.id = _new_id()
        self._records[record.id] = record
        return record

    def update(self, record: QARecord) -> QARecord:
        record.updated_at = _utcnow()
        record.version = self._records.get(record.id, record).version + 1
        self._records[record.id] = record
        return record

    def delete(self, record_id: str) -> bool:
        if record_id in self._records:
            del self._records[record_id]
            return True
        return False

    # ------------------------------------------------------------------
    # Publish workflow
    # ------------------------------------------------------------------

    def publish(self) -> dict:
        """Validate all records, persist to YAML, and report results.

        Returns a dict with keys:
          success (bool), errors (dict[id → list[str]]), count (int)
        """
        errors: Dict[str, List[str]] = {}
        for record in self._records.values():
            record_errors = record.validate()
            if record_errors:
                errors[record.id] = record_errors

        if errors:
            return {"success": False, "errors": errors, "count": 0}

        self._save()
        return {"success": True, "errors": {}, "count": len(self._records)}
