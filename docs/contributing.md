# Contributing to QAKey

Thank you for your interest in improving QAKey. This guide covers
content contributions (Q&A records) and code contributions.

---

## Contributing Q&A content

Content contributions are the most impactful way to improve QAKey for
your organization. You do not need coding or repository knowledge.

### Using the Content Editor (recommended)

1. Open `/editor` in your browser.
2. Click **New Record** and fill in the fields:
   - **Canonical Question** — the authoritative, single-best phrasing.
   - **Alternate Phrasings** — other ways users might ask the same thing (one per line).
   - **Answer** — the approved answer, written clearly and completely.
   - **Status** — set to `Draft` while the record is in review.
   - **Contributor** — your name or email.
3. Click **Save Record**.
4. Ask a reviewer to open the editor, verify the record, add their name as Reviewer, and change the status to `Active`.
5. The reviewer clicks **Publish Updates** to make the answer live.

### Directly editing YAML

For bulk imports or migration from an existing FAQ:

1. Edit `knowledge/qa_records.yaml` following the schema in [docs/schema.md](schema.md).
2. Do not set `id`, `created_at`, `updated_at`, or `version` — leave them blank or omit them; QAKey assigns these automatically on the next Publish.
3. Commit your changes and trigger a restart or call `POST /api/publish`.

---

## Contributing code

### Prerequisites

- Python 3.11 or later
- Git

### Setup

```bash
git clone https://github.com/your-org/QAKey.git
cd QAKey
pip install -r requirements.txt
```

### Running tests

```bash
python -m pytest tests/ -v
```

All tests must pass before submitting a pull request.

### Project structure

| Module | Responsibility |
|---|---|
| `qakey/models.py` | `QARecord` dataclass, validation |
| `qakey/store.py` | YAML I/O, CRUD, publish workflow |
| `qakey/engine.py` | Text processing, TF-IDF index, matching |
| `app.py` | Flask routes and application wiring |
| `templates/` | Jinja2 HTML templates |
| `static/` | CSS and vanilla JavaScript |

### Code style

- Follow PEP 8.
- Use type annotations for all function signatures.
- Keep functions small and single-purpose.
- Document public methods with docstrings.

### Pull request checklist

- [ ] All existing tests pass (`python -m pytest tests/ -v`)
- [ ] New behaviour is covered by tests
- [ ] `config.yaml` or schema changes are reflected in the relevant `docs/` file
- [ ] No secrets or credentials in the commit

---

## Reporting issues

Open a GitHub issue with:

- A clear description of the problem or enhancement request.
- Steps to reproduce (for bugs).
- The relevant section of `config.yaml` (redact any sensitive values).
- The Python and Flask version (`python --version`, `pip show flask`).
