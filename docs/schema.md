# QAKey Knowledge Base Schema

## `knowledge/qa_records.yaml`

The records file is a YAML document with a single top-level key: `records`.

```yaml
records:
  - id: "qa-0001"
    canonical_question: "What are your business hours?"
    alternate_phrasings:
      - "When are you open?"
      - "What time do you open?"
      - "Hours of operation"
    answer: >
      We are open Monday through Friday, 9 AM to 5 PM Eastern Time.
    status: "Active"
    contributor: "staff@example.com"
    reviewer: "admin@example.com"
    tags:
      - "hours"
      - "contact"
    created_at: "2024-01-01T00:00:00Z"
    updated_at: "2024-01-01T00:00:00Z"
    version: 1
```

---

## Field reference

| Field | Required | Managed by | Description |
|---|---|---|---|
| `id` | Yes | Auto | Unique identifier (`qa-<8 hex chars>`). Never edit manually. |
| `canonical_question` | **Yes** | Maintainer | The authoritative, single-best phrasing of the question. |
| `alternate_phrasings` | No | Maintainer | Other ways users might phrase the same question. The more you add, the better the matching. |
| `answer` | **Yes** | Maintainer | The approved, golden answer. Returned verbatim. |
| `status` | **Yes** | Maintainer | `Draft`, `Active`, or `Inactive`. Only `Active` records are indexed and returned. |
| `contributor` | No | Maintainer | Name or email of the person who authored or proposed this record. |
| `reviewer` | No | Maintainer | Name or email of the person who approved this record. |
| `tags` | No | Maintainer | Free-form labels for grouping and filtering. Not used by the matching engine. |
| `created_at` | Yes | Auto | ISO-8601 UTC timestamp, set on creation. |
| `updated_at` | Yes | Auto | ISO-8601 UTC timestamp, updated on every save. |
| `version` | Yes | Auto | Integer counter, incremented on every update. |

---

## Status lifecycle

```
 ┌───────┐    review     ┌────────┐    retire    ┌──────────┐
 │ Draft │ ────────────► │ Active │ ──────────► │ Inactive │
 └───────┘               └────────┘             └──────────┘
                              │
                              │ returns answers
                              ▼
                          end users
```

- **Draft** — record is being worked on; not visible to end users.
- **Active** — record is indexed and its answer is returned to users.
- **Inactive** — record is retired; retained for audit purposes but not indexed.

---

## `knowledge/synonyms.yaml`

The synonyms file maps a canonical (stemmed) token to a list of equivalent terms.
The engine applies the same stemmer to both the map keys and the values, so minor
inflection differences are handled automatically.

```yaml
synonyms:
  vacation:
    - pto
    - leave
    - holiday
    - time-off
  password:
    - credential
    - login
    - access
```

### Tips for synonym management

- Use the **stemmed** form of the canonical token as the key (e.g. `employ` not `employees`).
- Include acronyms and abbreviations your users commonly use (e.g. `pto` for "paid time off").
- Add product names, team names, or internal jargon specific to your organization.
- Rebuild the index (click **Publish Updates**) after editing this file.

---

## Editing the knowledge base

### Option A — Content Editor (recommended for non-technical maintainers)

1. Open `http://your-server/editor`.
2. Click **New Record** to add a Q&A pair, or click the edit icon on any existing row.
3. Fill in the fields in the modal dialog.
4. Set status to **Active** when the record is ready.
5. Click **Publish Updates** to validate, save, and rebuild the index.

### Option B — Direct YAML edit (for technical maintainers)

1. Edit `knowledge/qa_records.yaml` directly.
2. Restart the application (or call `POST /api/publish` via the API) to rebuild the index.

> **Note:** IDs, timestamps, and version numbers are managed by QAKey. Do not edit them manually.
