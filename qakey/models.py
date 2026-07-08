"""Data models for QAKey records."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


VALID_STATUSES = ("Draft", "Active", "Inactive")


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id() -> str:
    return f"qa-{uuid.uuid4().hex[:8]}"


@dataclass
class QARecord:
    """A single Q&A knowledge-base entry."""

    id: str
    canonical_question: str
    answer: str
    status: str  # Draft | Active | Inactive
    alternate_phrasings: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    contributor: str = ""
    reviewer: str = ""
    created_at: str = ""
    updated_at: str = ""
    version: int = 1

    def __post_init__(self) -> None:
        if not self.id:
            self.id = _new_id()
        now = _utcnow()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = self.created_at

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "canonical_question": self.canonical_question,
            "answer": self.answer,
            "status": self.status,
            "alternate_phrasings": self.alternate_phrasings,
            "tags": self.tags,
            "contributor": self.contributor,
            "reviewer": self.reviewer,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QARecord":
        return cls(
            id=data.get("id", ""),
            canonical_question=data.get("canonical_question", ""),
            answer=data.get("answer", ""),
            status=data.get("status", "Draft"),
            alternate_phrasings=data.get("alternate_phrasings") or [],
            tags=data.get("tags") or [],
            contributor=data.get("contributor", ""),
            reviewer=data.get("reviewer", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            version=int(data.get("version", 1)),
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> List[str]:
        """Return a list of validation error messages (empty means valid)."""
        errors: List[str] = []
        if not self.canonical_question.strip():
            errors.append("canonical_question is required")
        if not self.answer.strip():
            errors.append("answer is required")
        if self.status not in VALID_STATUSES:
            errors.append(
                f"status must be one of {VALID_STATUSES} (got '{self.status}')"
            )
        return errors
