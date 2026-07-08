# QAKey Implementation Guide

## Overview

QAKey is structured as three loosely coupled layers:

1. **Data layer** (`qakey/store.py`, `qakey/models.py`) — reads, writes, and validates records
2. **Engine layer** (`qakey/engine.py`) — builds a search index and matches queries
3. **Application layer** (`app.py`, templates, static) — exposes the UI and REST API

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
| `GET /editor` | `editor()` | Renders `templates/editor.html` |
| `POST /api/query` | `api_query()` | `{"question": "..."}` → `MatchResult` |
| `GET /api/records` | `api_list_records()` | Returns all records as JSON |
| `POST /api/records` | `api_create_record()` | Creates a record in memory |
| `PUT /api/records/<id>` | `api_update_record()` | Updates a record in memory |
| `DELETE /api/records/<id>` | `api_delete_record()` | Deletes a record from memory |
| `POST /api/publish` | `api_publish()` | Validates, saves, rebuilds index |
| `GET /api/health` | `api_health()` | Health check |

### Frontend

The query interface (`static/js/app.js`) sends POST requests to `/api/query` and renders the result. A session history of recent queries is maintained in memory.

The editor (`static/js/editor.js`) loads all records on page load and manages them through the REST API. Add, edit, and delete operations update memory immediately; changes are reflected in the table. The **Publish Updates** button calls `/api/publish`.

---

## Adding a new deployment interface

QAKey's core is deployment-agnostic. To add a Microsoft Teams bot, Slack integration, or any other interface:

1. Import `QAStore` and `QAEngine` from the `qakey` package.
2. Initialise them with your config.
3. Call `engine.match(user_message)` and return `result.answer` if `result.matched`.

The `MatchResult.to_dict()` method returns a standard JSON-serialisable dictionary for easy integration with any messaging platform.
