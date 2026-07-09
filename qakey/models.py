"""Data models for QAKey records and query results."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


VALID_STATUSES = ("Draft", "Active", "Inactive")

VALID_FALLBACK_TYPES = (
    "empty_query",
    "no_match",
    "ambiguous",
    "no_active_records",
    "unavailable_record",
)


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

        self.status = self.status or "Draft"

        now = _utcnow()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = self.created_at

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        return self.status == "Active"

    @property
    def is_draft(self) -> bool:
        return self.status == "Draft"

    @property
    def is_inactive(self) -> bool:
        return self.status == "Inactive"

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
            id=str(data.get("id", "")).strip(),
            canonical_question=str(data.get("canonical_question", "")).strip(),
            answer=str(data.get("answer", "")).strip(),
            status=str(data.get("status", "Draft")).strip() or "Draft",
            alternate_phrasings=list(data.get("alternate_phrasings") or []),
            tags=list(data.get("tags") or []),
            contributor=str(data.get("contributor", "")).strip(),
            reviewer=str(data.get("reviewer", "")).strip(),
            created_at=str(data.get("created_at", "")).strip(),
            updated_at=str(data.get("updated_at", "")).strip(),
            version=int(data.get("version", 1)),
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> List[str]:
        """Return a list of validation error messages. Empty means valid."""
        errors: List[str] = []
        label = self.id or "Record"

        if not self.canonical_question.strip():
            errors.append(f"{label}: canonical_question is required")

        if not self.answer.strip():
            errors.append(f"{label}: answer is required")

        if self.status not in VALID_STATUSES:
            errors.append(
                f"{label}: status must be one of {VALID_STATUSES} "
                f"(got '{self.status}')"
            )

        return errors


@dataclass
class MatchSuggestion:
    """A safe canonical-question suggestion for ambiguous matches."""

    record_id: str
    canonical_question: str
    confidence: float

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "canonical_question": self.canonical_question,
            "confidence": round(self.confidence, 4),
        }


@dataclass
class MatchResult:
    """Normalized result returned by QAKey's matching engine.

    A result is either:

    - matched: one Active approved record met the confidence rules
    - fallback: QAKey could not safely return one approved answer
    """

    record: Optional[QARecord]
    confidence: float
    threshold: float
    status: str = "fallback"
    fallback_type: Optional[str] = None
    message: Optional[str] = None
    suggestions: List[MatchSuggestion] = field(default_factory=list)

    @property
    def matched(self) -> bool:
        return self.status == "matched" and self.record is not None

    def to_dict(self) -> dict:
        if not self.matched:
            return {
                "status": "fallback",
                "matched": False,
                "fallback_type": self.fallback_type,
                "confidence": round(self.confidence, 4),
                "threshold": round(self.threshold, 4),
                "answer": self.message,
                "canonical_question": None,
                "record_id": None,
                "suggestions": [s.to_dict() for s in self.suggestions],
            }

        return {
            "status": "matched",
            "matched": True,
            "fallback_type": None,
            "confidence": round(self.confidence, 4),
            "threshold": round(self.threshold, 4),
            "answer": self.record.answer,
            "canonical_question": self.record.canonical_question,
            "record_id": self.record.id,
            "suggestions": [],
        }
