# QAKey — Q&A Key ("Quackie") 🦆
## Active Development July 2026 - 🚧

QAKey is built to deliver reliable, approved answers in plain language, without requiring teams to run a full AI platform. It favors deterministic truth over open-ended generation, keeps knowledge ownership with people, and supports both small teams and larger organizations that need governance and auditability.

In practice, this means QAKey is designed to:

- Return approved answers predictably across channels
- Reduce repeated support questions and speed up onboarding
- Lower risk from outdated or inconsistent responses
- Shorten the path from policy change to published guidance

QAKey is not designed to be an autonomous policy decision-maker or a broad, generative answer engine beyond your approved knowledge base.

**A minimal, deterministic question-answering framework for organizations.**

QAKey maps naturally phrased user questions to canonical questions and returns the corresponding approved answer *exactly* as maintained in the knowledge base.
It does not generate answers — every response is deterministic and fully controlled.

It is designed for people who need reliable answers without running a full AI platform: website maintainers, internal ops teams, support teams, and "accidental tech" owners in nonprofits, schools, and small businesses.

---

## Why QAKey exists

Most teams do not actually need generated answers for core policy and process questions.
They need consistency, auditability, and fast updates by the people who own the content.

QAKey is built around a simple idea:

- Questions can be asked in many ways.
- Answers should come from one approved source of truth.
- Content owners should be able to update that source without developer bottlenecks.

---

## Current scope (July 8 2026)

QAKey currently provides a local web UI, a spreadsheet-like content editor, a YAML-backed knowledge store, a REST API, a deterministic matching engine, and a publish workflow. The framework is intentionally minimal: advanced enterprise features such as SSO, role-based permissions, analytics dashboards, and managed cloud deployment are treated as extension points rather than core requirements.

---

## Philosophy

### 1) Deterministic over creative

QAKey intentionally returns approved answers verbatim. This avoids hallucinations, policy drift, and "close enough" responses that can cause operational problems.

### 2) Human-owned knowledge

The system helps users find answers, but people own the answers. Subject matter experts and maintainers retain control over wording, status, and the review lifecycle.

### 3) Practical NLP, not model ops

Matching is based on lightweight NLP and synonyms, so teams can improve quality through better records and term mappings, rather than expensive retraining cycles.

### 4) Operational clarity

Every record has a status and metadata. You can explain where an answer came from, who updated it, and when it changed.

### 5) AI accessibility

QAKey treats accessibility as an architectural requirement. The people who know the answers should be able to maintain the answers. A maintainer should not need to understand code, YAML, embeddings, model operations, or deployment pipelines to keep approved information up to date.

Technical teams can extend QAKey with stronger governance, integrations, authentication, analytics, or deployment controls, but those capabilities should add power without making technical expertise the price of participation.

---

## Expected outcomes

Teams typically use QAKey to achieve outcomes like:

- Fewer repeated "where do I find..." or "what is our policy on..." questions
- Faster onboarding for staff, volunteers, and rotating support members
- More consistent answers across channels (website, chatbot, internal tools)
- Lower risk from inconsistent or outdated responses
- Shorter turnaround from policy change to published answer

In short: less answer chaos, more confidence.

---

## Why it is a strong fit for small teams

If you are the "techy" person in a nonprofit or small organization, QAKey is built for your reality:

- Minimal stack: Python + YAML + Flask, easy to run and reason about
- Non-developer editing: content can be maintained in the built-in editor
- Deterministic behavior: easier to trust and explain to leadership
- Low maintenance: no prompt engineering pipelines or model tuning required
- Incremental adoption: start with a small FAQ and grow safely over time

You can deliver useful, reliable Q&A without becoming an AI platform team.

---

## Why it also works inside larger organizations

Large organizations often need controlled, auditable knowledge delivery. QAKey supports that model while staying simple:

- Governance-friendly: approved answers, lifecycle states, and reviewer metadata
- Integration-ready: REST API for portals, chat surfaces, and internal assistants
- Domain adaptable: synonym mapping supports business language and abbreviations
- Deployment-flexible: run as a service, embed in existing products, or expose via API
- Team separation: policy owners maintain content while engineering manages integration

QAKey can be a practical "trusted answer layer" inside a broader knowledge architecture.

---

## Features 🦆

| Capability | Description |
|---|---|
| **Natural-language input** | Intent classification, synonym normalization, semantic matching, and confidence scoring |
| **Deterministic output** | Approved answers are returned verbatim — no generation, no hallucination |
| **User-facing front page** | Dedicated user-side query UI with light/dark/system mode controls and explicit AI usage messaging |
| **Spreadsheet-like editor** | Non-technical maintainers can add, edit, inspect, and sunset records in a web UI |
| **Staged publish workflow** | Tracks unpublished changes, supports undo, and publishes validated updates in one action |
| **Status management** | Draft → Active → Inactive lifecycle for every record |
| **Audit fields** | Contributor, reviewer, version, created/updated timestamps — all automatic |
| **Import and export** | CSV/XLSX import preview and CSV/XLSX export for audit and record keeping |
| **Editor access boundary** | Optional admin/password gate for `/editor`, extensible to enterprise auth layers |
| **Synonym support** | Domain-specific terms and abbreviations handled transparently |
| **REST API** | All operations available as JSON endpoints |
| **Deployment-agnostic** | Web UI, API, chatbot integration, or embedded widget |

---

## Source-of-Truth Framework

QAKey is built around a spreadsheet-like editing model for maintainers who should not need knowledge of coding, repositories, or YAML.
They manage the approved question, answer, status, and review ownership, while QAKey handles identifiers, timestamps, validation, versioning, persistence, and index rebuilds automatically.

See [docs/source-of-truth-framework.md](docs/source-of-truth-framework.md) for the full framework and maintainer workflow.

---

## Is QAKey the right tool?

QAKey is a great fit when:

- You need high-confidence answers from approved content
- You want non-developers to maintain knowledge safely
- You value transparency and predictable behavior over open-ended generation

It may be a weaker fit when:

- You need broad, generative responses beyond a defined knowledge base
- You do not have owners who can keep canonical answers current
- You want autonomous agents making policy decisions

---

## Quick start

### 1 — Clone or fork the repository

```bash
git clone https://github.com/your-org/QAKey.git
cd QAKey
```

### 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### 3 — Replace the sample content

Edit [`knowledge/qa_records.yaml`](knowledge/qa_records.yaml) with your own Q&A pairs,
or use the built-in Content Editor (step 5).

### 4 — Configure the application

Edit [`config.yaml`](config.yaml) to set your organization name, confidence threshold,
and other options.

### 5 — Run the application

```bash
python app.py
```

Optional editor auth setup:

```bash
export QAKEY_EDITOR_USERNAME="admin"
export QAKEY_EDITOR_PASSWORD="change-me"
```

Open **http://127.0.0.1:5000** to ask questions and
**http://127.0.0.1:5000/editor** to manage the knowledge base.

---

## Current Repository structure 🦆

```
QAKey/
├── app.py                  Flask web application
├── config.yaml             Application configuration
├── requirements.txt        Python dependencies
│
├── qakey/                  Core Python package
│   ├── engine.py           NLP matching engine (TF-IDF, synonyms, confidence)
│   ├── ingest.py           Deterministic source text parsing helpers
│   ├── models.py           QARecord data model with validation
│   ├── rendering.py        Safe answer rendering helpers (markdown + sanitization)
│   └── store.py            YAML-backed data store with publish workflow
│
├── knowledge/              Knowledge base (replace with your content)
│   ├── qa_records.yaml     Canonical questions, answers, status, metadata
│   └── synonyms.yaml       Domain synonym mappings
│
├── templates/
│   ├── base.html           Shared layout
│   ├── editor_login.html   Optional editor auth login page
│   ├── index.html          Query interface (end-user)
│   └── editor.html         Content editor (maintainer)
│
├── static/
│   ├── css/style.css
│   └── js/
│       ├── app.js          Query interface behaviour
│       └── editor.js       Editor behaviour
│
├── tests/
│   ├── conftest.py         Shared fixtures
│   ├── test_app_rendering.py
│   ├── test_engine.py      Engine and NLP unit + integration tests
│   ├── test_ingest.py
│   ├── test_rendering.py
│   └── test_store.py       Store and model tests
│
└── docs/
    ├── implementation.md   How the application works
    ├── configuration.md    Configuration reference
    ├── schema.md           Knowledge base schema reference
    ├── deployment.md       Deployment options
    └── contributing.md     Contribution guidelines
```

---

## Interfaces

QAKey ships with a **web UI** and a **REST API**.

### Query interface (`/`)

End-users type a question naturally. QAKey returns the matched approved answer with a confidence score, or a configurable no-match message.

### Content editor (`/editor`)

Maintainers manage the knowledge base in a spreadsheet-like table without touching
YAML or code:

1. **Add** a new record with canonical question, alternates, answer, and status.
2. **Edit/Inspect** fields and metadata (including contributor/reviewer ownership).
3. **Import** records from CSV/XLSX with preview and defaults (optional accelerator, not the primary path).
4. **Export** records to CSV/XLSX for auditing.
5. **Stage** unpublished changes with an explicit publish summary and ID-level entries.
6. Click **Publish Updates** to validate all records, save to YAML, and rebuild the index.

When `editor.require_auth` is enabled, `/editor` is protected by a built-in admin/password login. This simple model can be replaced by an organization auth later.

### REST API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/query` | Match a question → answer |
| `GET` | `/api/records` | List all records |
| `POST` | `/api/records` | Create a record |
| `PUT` | `/api/records/<id>` | Update a record |
| `DELETE` | `/api/records/<id>` | Delete a record |
| `POST` | `/api/records/import-preview` | Preview records parsed from CSV/XLSX |
| `GET` | `/api/records/export?format=csv|xlsx` | Export records for audit/archival |
| `POST` | `/api/ingest/preview` | Preview deterministic raw text parsing |
| `POST` | `/api/publish` | Validate, persist, and rebuild index |

---

## How matching works

1. **Normalize** — lowercase, expand contractions, remove punctuation
2. **Tokenize** — split on whitespace
3. **Stopwords** — remove common English function words
4. **Stem** — simple suffix-stripping (no external library required)
5. **Synonyms** — expand tokens using `knowledge/synonyms.yaml`
6. **TF-IDF cosine similarity** — score each active record against the query
7. **Confidence threshold** — return the best match if confidence ≥ threshold

Scores range from 0 to 1. The threshold is configurable in `config.yaml`.

---

## Running tests

```bash
python -m pytest tests/ -v
```

Workflow-focused tests:

- `tests/test_editor_query_workflow.py` validates the editor lifecycle (add/edit/refine/status changes) and user query behavior before/after publish.
- `tests/test_import_preview_workflow.py` validates XLSX import preview using a fixture in `tests/fixtures/`.

## Documentation

- [docs/source-of-truth-framework.md](docs/source-of-truth-framework.md) — maintainer operating model and publish workflow
- [docs/implementation.md](docs/implementation.md) — architecture, routes, and UI behavior
- [docs/configuration.md](docs/configuration.md) — configuration and environment variables
- [docs/schema.md](docs/schema.md) — knowledge record schema and lifecycle semantics
- [docs/deployment.md](docs/deployment.md) — runtime/deployment guidance and editor security boundary
- [docs/contributing.md](docs/contributing.md) — content and code contribution workflow

---

## License

MIT
