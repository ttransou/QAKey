# QAKey Implementation Guide

## Overview

QAKey is structured as four loosely coupled layers:

1. **Data layer** (`qakey/store.py`, `qakey/models.py`) — reads, writes, and validates records
2. **Ingest layer** (`qakey/ingest.py`) — deterministically extracts, chunks, and parses raw source text
3. **Engine layer** (`qakey/engine.py`) — builds a search index and matches queries
4. **Application layer** (`app.py`, templates, static) — exposes the UI and REST API

---

## Data layer

### `QARecord` (models.py)

Each knowledge-base entry is a `QARecord` dataclass with these fields:

| Field | Type | Set by |
|---|---|---|
| `id` | string | Auto-generated (`qa-<8 hex chars>`) |
| `canonical_question` | string | Maintainer |
| `answer` | string | Maintainer |
| `status` | `Draft` / `Active` / `Inactive` | Maintainer |
| `alternate_phrasings` | list of strings | Maintainer |
| `tags` | list of strings | Maintainer |
| `contributor` | string | Maintainer |
| `reviewer` | string | Maintainer |
| `created_at` | ISO-8601 UTC | Auto-set on creation |
| `updated_at` | ISO-8601 UTC | Auto-updated on every change |
| `version` | integer | Auto-incremented on every update |

`QARecord.validate()` returns a list of error messages. An empty list means the record is valid.

### `QAStore` (store.py)

`QAStore` wraps the YAML file at `config.knowledge.records_path`. It provides:

- `get_all()` — all records regardless of status
- `get_active()` — only `Active` records (used by the engine)
- `get(id)`, `create()`, `update()`, `delete()` — standard CRUD
- `publish()` — validates all records, saves to YAML, and returns results

Changes made through CRUD methods are held **in memory** until `publish()` is called. This allows maintainers to make multiple edits and preview them before committing.

---

## Ingest layer

### `qakey.ingest`

The ingest helpers support bulk import of user-provided source text without introducing generation.

**Operational flow**

1. **Extract** — normalize pasted text into consistent newline-delimited blocks.
2. **Chunk** — group adjacent blocks into stable chunks up to a fixed character budget.
3. **Deterministically retrieve** — for each question-shaped block, retrieve the answer from the same block or the immediately following non-question blocks.
4. **Parse** — emit candidate Q&A records only when the structure is explicit enough to be trusted.

**Accepted deterministic patterns**

- `Question: ...` followed by `Answer: ...`
- `Q: ...` followed by `A: ...`
- A single-line question ending in `?` followed by answer text in the same block or the next block

Free-form prose that does not expose a deterministic question-answer structure is ignored during import preview.

**Primary helpers**

- `extract_blocks(raw_text)` — split source text into paragraph-like blocks
- `chunk_text(raw_text, max_chars=650)` — group blocks into stable import chunks
- `parse_chunks(chunks)` — convert chunks into parsed Q&A candidates
- `build_records_from_text(...)` — produce draft `QARecord` objects with supplied metadata

---

## Engine layer

### `QAEngine` (engine.py)

The engine is initialized with a list of active records and an optional synonym dictionary.

**Index building (`_build_index`)**

For every active record the engine concatenates the canonical question and all alternate phrasings, runs them through the full text-processing pipeline, and stores the resulting token list. Document-frequency counts are computed over the corpus to derive IDF weights.

**Text processing pipeline**

```
raw text
  → expand contractions ("don't" → "do not")
  → lowercase
  → remove punctuation
  → tokenize (split on whitespace)
  → remove stopwords
  → simple suffix-strip stemming ("working" → "work")
  → synonym expansion (optional)
```

**Matching (`engine.match(query)`)**

1. Run the query through the same text-processing pipeline.
2. Compute TF-IDF cosine similarity between the query vector and each document vector.
3. Return the record with the highest score if it meets or exceeds `confidence_threshold`.
4. Otherwise return a no-match result with the raw score for diagnostics.

**`engine.rebuild(records)`**

Called automatically after a successful publish. Reinitialises the index with the new set of active records.

---

## Application layer

### Flask routes (`app.py`)

| Route | Handler | Notes |
|---|---|---|
| `GET /` | `index()` | Renders `templates/index.html` |
| `GET/POST /editor/login` | `editor_login()` | Optional editor auth entry-point |
| `POST /editor/logout` | `editor_logout()` | Ends editor auth session |
| `GET /editor` | `editor()` | Renders `templates/editor.html` |
| `POST /api/query` | `api_query()` | `{"question": "..."}` → `MatchResult` |
| `GET /api/records` | `api_list_records()` | Returns all records as JSON |
| `POST /api/records` | `api_create_record()` | Creates a record in memory |
| `PUT /api/records/<id>` | `api_update_record()` | Updates a record in memory |
| `DELETE /api/records/<id>` | `api_delete_record()` | Deletes a record from memory |
| `POST /api/records/import-preview` | `api_import_preview()` | Parses CSV/XLSX records for preview before import |
| `GET /api/records/export?format=csv|xlsx` | `api_records_export()` | Exports records for audit and archiving |
| `POST /api/ingest/preview` | `api_ingest_preview()` | Extracts, chunks, and parses pasted source text into preview records |
| `POST /api/publish` | `api_publish()` | Validates, saves, rebuilds index |
| `GET /api/health` | `api_health()` | Health check |

### Frontend

The query interface (`static/js/app.js`) sends POST requests to `/api/query` and renders the result. A session history of recent queries is maintained in memory. The front page includes user-side-only messaging and a light/dark/system mode toggle.

The editor (`static/js/editor.js`) loads all records on page load and manages them through the REST API. Add, edit, delete, sunset, and import operations update in-memory staged changes immediately; changes are reflected in the table and in the Publishing Stage panel. The editor supports:

- CSV/XLSX import preview before record creation
- CSV/XLSX export for audit and record keeping
- Undo-last-change for staged unpublished operations
- ID-level publishing-stage visibility before commit

Editor-first note: the normal ingestion path is direct record maintenance in the Content Editor. CSV/XLSX import is supported as a secondary accelerator for bulk onboarding or migration.

The **Publish Updates** and **Publish Staged Changes** actions call `/api/publish`.

---

## Workflow test coverage

QAKey includes explicit workflow tests for end-to-end behavior:

- `tests/test_editor_query_workflow.py` simulates add/edit/refine/deactivate in editor APIs and verifies user-side query behavior before and after publish.
- `tests/test_import_preview_workflow.py` validates spreadsheet import preview behavior against a real XLSX fixture.

---

## Adding a new deployment interface

QAKey's core is deployment-agnostic. To add a Microsoft Teams bot, Slack integration, or any other interface:

1. Import `QAStore` and `QAEngine` from the `qakey` package.
2. Initialise them with your config.
3. Call `engine.match(user_message)` and return `result.answer` if `result.matched`.

The `MatchResult.to_dict()` method returns a standard JSON-serialisable dictionary for easy integration with any messaging platform.
