"""Shared pytest fixtures for QAKey tests."""

import pytest

from qakey.models import QARecord


@pytest.fixture
def sample_records():
    return [
        QARecord(
            id="qa-t001",
            canonical_question="What are your business hours?",
            alternate_phrasings=["When are you open?", "Office hours"],
            answer="We are open Monday–Friday 9–5 ET.",
            status="Active",
        ),
        QARecord(
            id="qa-t002",
            canonical_question="How do I reset my password?",
            alternate_phrasings=["Forgot password", "Lost access to account"],
            answer="Click Forgot Password on the login page.",
            status="Active",
        ),
        QARecord(
            id="qa-t003",
            canonical_question="What is the vacation policy?",
            alternate_phrasings=["How many PTO days do I get?", "Annual leave"],
            answer="Full-time employees receive 15 days per year.",
            status="Active",
        ),
        QARecord(
            id="qa-t004",
            canonical_question="Draft: upcoming pet policy",
            alternate_phrasings=[],
            answer="Pets are allowed on Fridays.",
            status="Draft",
        ),
    ]
