"""Deterministic ingestion helpers for bulk Q&A import."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from .models import QARecord


QUESTION_PREFIX_RE = re.compile(r"^(?:q|question)\s*[:\-]\s*(.+)$", re.IGNORECASE)
ANSWER_PREFIX_RE = re.compile(r"^(?:a|answer)\s*[:\-]\s*(.*)$", re.IGNORECASE)


@dataclass
class ParsedCandidate:
    canonical_question: str
    answer: str
    chunk_index: int
    source_excerpt: str

    def to_dict(self) -> dict:
        return {
            "canonical_question": self.canonical_question,
            "answer": self.answer,
            "chunk_index": self.chunk_index,
            "source_excerpt": self.source_excerpt,
        }

    def to_record(
        self,
        *,
        status: str = "Draft",
        contributor: str = "",
        reviewer: str = "",
        tags: Optional[List[str]] = None,
    ) -> QARecord:
        return QARecord(
            id="",
            canonical_question=self.canonical_question,
            answer=self.answer,
            status=status,
            alternate_phrasings=[],
            tags=list(tags or []),
            contributor=contributor,
            reviewer=reviewer,
        )


def extract_text(raw_text: str) -> str:
    """Normalise newlines and trim wrapper whitespace."""
    text = (raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def extract_blocks(raw_text: str) -> List[str]:
    """Split extracted text into paragraph-like blocks."""
    text = extract_text(raw_text)
    if not text:
        return []
    return [block.strip("\n") for block in re.split(r"\n\s*\n", text) if block.strip()]


def chunk_text(raw_text: str, max_chars: int = 650) -> List[str]:
    """Build stable chunks by grouping nearby blocks up to *max_chars*."""
    blocks = extract_blocks(raw_text)
    if not blocks:
        return []

    chunks: List[str] = []
    current: List[str] = []
    current_size = 0

    for block in blocks:
        block_size = len(block)
        would_exceed = bool(current) and current_size + 2 + block_size > max_chars
        if would_exceed:
            chunks.append("\n\n".join(current))
            current = []
            current_size = 0

        current.append(block)
        current_size = current_size + (2 if current_size else 0) + block_size

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def parse_chunks(chunks: List[str]) -> List[ParsedCandidate]:
    """Parse deterministic Q&A candidates from chunked source text."""
    candidates: List[ParsedCandidate] = []

    for chunk_index, chunk in enumerate(chunks):
        blocks = [block for block in extract_blocks(chunk) if block]
        i = 0
        while i < len(blocks):
            question = _extract_question(blocks[i])
            if question is None:
                i += 1
                continue

            answer_parts, next_index = _collect_answer_blocks(blocks, i)
            answer = "\n\n".join(part for part in answer_parts if part).strip()
            if answer:
                candidates.append(
                    ParsedCandidate(
                        canonical_question=question,
                        answer=answer,
                        chunk_index=chunk_index,
                        source_excerpt=_make_excerpt(blocks[i]),
                    )
                )
            i = next_index

    return candidates


def build_records_from_text(
    raw_text: str,
    *,
    status: str = "Draft",
    contributor: str = "",
    reviewer: str = "",
    tags: Optional[List[str]] = None,
    max_chars: int = 650,
) -> List[QARecord]:
    """Convert raw source text into draft QA records using deterministic rules."""
    candidates = parse_chunks(chunk_text(raw_text, max_chars=max_chars))
    return [
        candidate.to_record(
            status=status,
            contributor=contributor,
            reviewer=reviewer,
            tags=tags,
        )
        for candidate in candidates
    ]


def _extract_question(block: str) -> Optional[str]:
    lines = [line.strip() for line in block.split("\n") if line.strip()]
    if not lines:
        return None

    match = QUESTION_PREFIX_RE.match(lines[0])
    if match:
        return _clean_question(match.group(1))

    first_line = lines[0]
    if first_line.endswith("?"):
        return _clean_question(first_line)

    return None


def _collect_answer_blocks(blocks: List[str], index: int) -> tuple[List[str], int]:
    current_block = blocks[index]
    lines = current_block.split("\n")
    answer_in_block = _extract_inline_answer(lines)
    if answer_in_block is not None:
        return [answer_in_block], index + 1

    next_index = index + 1
    answer_parts: List[str] = []
    while next_index < len(blocks):
        if _extract_question(blocks[next_index]) is not None:
            break
        answer_parts.append(_strip_answer_prefixes(blocks[next_index]))
        next_index += 1

    return answer_parts, next_index


def _strip_answer_prefixes(block: str) -> str:
    lines = block.split("\n")
    cleaned: List[str] = []
    for line in lines:
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        match = ANSWER_PREFIX_RE.match(stripped)
        cleaned.append(indent + match.group(1) if match else line)
    return _trim_blank_edges("\n".join(cleaned))


def _extract_inline_answer(lines: List[str]) -> Optional[str]:
    if len(lines) <= 1:
        return None

    answer_lines = lines[1:]
    first_content_index = _first_non_empty_line(answer_lines)
    if first_content_index is None:
        return None

    first_line = answer_lines[first_content_index]
    stripped = first_line.lstrip()
    indent = first_line[: len(first_line) - len(stripped)]
    answer_match = ANSWER_PREFIX_RE.match(stripped)

    cleaned_lines = answer_lines[:]
    if answer_match:
        cleaned_lines[first_content_index] = indent + answer_match.group(1)

    return _trim_blank_edges("\n".join(cleaned_lines))


def _first_non_empty_line(lines: List[str]) -> Optional[int]:
    for index, line in enumerate(lines):
        if line.strip():
            return index
    return None


def _trim_blank_edges(text: str) -> str:
    lines = text.split("\n")
    start = 0
    end = len(lines)

    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1

    return "\n".join(lines[start:end])


def _clean_question(question: str) -> str:
    question = re.sub(r"\s+", " ", question).strip()
    if question and not question.endswith("?"):
        question += "?"
    return question


def _make_excerpt(block: str, max_chars: int = 140) -> str:
    compact = re.sub(r"\s+", " ", block).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."