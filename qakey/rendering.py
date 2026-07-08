"""Safe rendering helpers for maintainer-authored answers."""

from __future__ import annotations

import re

import bleach
from markdown import markdown


ALLOWED_TAGS = [
    "a",
    "blockquote",
    "br",
    "code",
    "em",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel", "target"],
    "th": ["align"],
    "td": ["align"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]
UNSAFE_BLOCK_RE = re.compile(
    r"<\s*(script|style)\b[^>]*>.*?<\s*/\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)


def render_answer_html(answer: str) -> str:
    """Render maintainer-authored markdown into sanitized HTML."""
    source = (answer or "").strip()
    if not source:
        return ""

    source = UNSAFE_BLOCK_RE.sub("", source)

    rendered = markdown(
        source,
        extensions=["extra", "sane_lists", "nl2br", "tables"],
        output_format="html5",
    )
    cleaned = bleach.clean(
        rendered,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return bleach.linkify(cleaned)