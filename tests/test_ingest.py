"""Tests for deterministic bulk-ingest helpers."""

from qakey.ingest import build_records_from_text, chunk_text, extract_blocks, parse_chunks


def test_extract_blocks_splits_paragraphs():
    raw = "First block\nline 2\n\nSecond block\n\n  \nThird"
    assert extract_blocks(raw) == [
        "First block\nline 2",
        "Second block",
        "Third",
    ]


def test_chunk_text_groups_blocks_under_limit():
    raw = (
        "Question: One?\nAnswer: First.\n\n"
        "Question: Two?\nAnswer: Second.\n\n"
        "Question: Three?\nAnswer: Third."
    )
    chunks = chunk_text(raw, max_chars=45)
    assert len(chunks) == 3
    assert chunks[0].startswith("Question: One?")


def test_parse_chunks_reads_prefixed_and_question_heading_formats():
    raw = (
        "Question: What are your support hours?\n"
        "Answer: Support is staffed Monday through Friday, 9 AM to 5 PM ET.\n\n"
        "How do I reset my password?\n"
        "Use the Forgot Password link on the sign-in page.\n\n"
        "This prose paragraph has no deterministic question shape."
    )

    candidates = parse_chunks(chunk_text(raw, max_chars=200))

    assert len(candidates) == 2
    assert candidates[0].canonical_question == "What are your support hours?"
    assert "Monday through Friday" in candidates[0].answer
    assert candidates[1].canonical_question == "How do I reset my password?"
    assert candidates[1].answer == "Use the Forgot Password link on the sign-in page."


def test_build_records_from_text_assigns_metadata():
    raw = "How do I submit an expense report?\nUse the Finance portal."
    records = build_records_from_text(
        raw,
        status="Active",
        contributor="alice",
        reviewer="bob",
        tags=["finance", "policy"],
    )

    assert len(records) == 1
    record = records[0]
    assert record.canonical_question == "How do I submit an expense report?"
    assert record.answer == "Use the Finance portal."
    assert record.status == "Active"
    assert record.contributor == "alice"
    assert record.reviewer == "bob"
    assert record.tags == ["finance", "policy"]


def test_parse_chunks_preserves_bullet_list_formatting():
    raw = (
        "Question: What is included in onboarding?\n"
        "Answer:\n"
        "- Laptop setup\n"
        "- Security training\n"
        "  - MFA enrollment\n"
        "- Handbook review"
    )

    candidates = parse_chunks(chunk_text(raw, max_chars=400))

    assert len(candidates) == 1
    assert candidates[0].answer == (
        "- Laptop setup\n"
        "- Security training\n"
        "  - MFA enrollment\n"
        "- Handbook review"
    )


def test_parse_chunks_preserves_markdown_table_formatting():
    raw = (
        "What are the support tiers?\n"
        "| Tier | Response time |\n"
        "| --- | --- |\n"
        "| P1 | 1 hour |\n"
        "| P2 | 4 hours |"
    )

    candidates = parse_chunks(chunk_text(raw, max_chars=400))

    assert len(candidates) == 1
    assert candidates[0].answer == (
        "| Tier | Response time |\n"
        "| --- | --- |\n"
        "| P1 | 1 hour |\n"
        "| P2 | 4 hours |"
    )