"""Tests for safe answer rendering."""

from qakey.rendering import render_answer_html


def test_render_answer_html_renders_lists_and_tables():
    answer = (
        "- First item\n"
        "- Second item\n\n"
        "| Tier | Response |\n"
        "| --- | --- |\n"
        "| P1 | 1 hour |"
    )

    rendered = render_answer_html(answer)

    assert "<ul>" in rendered
    assert "<li>First item</li>" in rendered
    assert "<table>" in rendered
    assert "<td>P1</td>" in rendered


def test_render_answer_html_strips_unsafe_html():
    rendered = render_answer_html("Hello<script>alert(1)</script><b>there</b>")

    assert "<script>" not in rendered
    assert "alert(1)" not in rendered
    assert "<b>" not in rendered
    assert "Hellothere" in rendered