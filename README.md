# QAKey — Q&A Key ("Quackie")

**A minimal, deterministic question-answering framework for organizations.**

QAKey maps naturally phrased user questions to canonical questions and returns
the corresponding approved answer *exactly* as maintained in the knowledge base.
It does not generate answers — every response is deterministic and fully controlled.

---

## Features

| Capability | Description |
|---|---|
| **Natural-language input** | Intent classification, synonym normalization, semantic matching, and confidence scoring |
| **Deterministic output** | Approved answers are returned verbatim — no generation, no hallucination |
| **Spreadsheet-like editor** | Non-technical maintainers can add, edit, and publish records in a web UI |
| **Publish workflow** | Validates records, persists to YAML, and rebuilds the index in one click |
| **Status management** | Draft → Active → Inactive lifecycle for every record |
| **Audit fields** | Contributor, reviewer, version, created/updated timestamps — all automatic |
| **Synonym support** | Domain-specific terms and abbreviations handled transparently |
| **REST API** | All operations available as JSON endpoints |
| **Deployment-agnostic** | Web UI, API, chatbot integration, or embedded widget |

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

Open **http://127.0.0.1:5000** to ask questions and
**http://127.0.0.1:5000/editor** to manage the knowledge base.

---

## Repository structure

```
QAKey/
├── app.py                  Flask web application
├── config.yaml             Application configuration
├── requirements.txt        Python dependencies
│
├── qakey/                  Core Python package
│   ├── engine.py           NLP matching engine (TF-IDF, synonyms, confidence)
│   ├── models.py           QARecord data model with validation
│   └── store.py            YAML-backed data store with publish workflow
│
├── knowledge/              Knowledge base (replace with your content)
│   ├── qa_records.yaml     Canonical questions, answers, status, metadata
│   └── synonyms.yaml       Domain synonym mappings
│
├── templates/
│   ├── base.html           Shared layout
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
│   ├── test_engine.py      Engine and NLP unit + integration tests
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

End-users type a question naturally. QAKey returns the matched approved answer
with a confidence score, or a configurable no-match message.

### Content editor (`/editor`)

Maintainers manage the knowledge base in a spreadsheet-like table without touching
YAML or code:

1. **Add** a new record with canonical question, alternates, answer, and status.
2. **Edit** any field in a modal dialog.
3. **Delete** records.
4. Click **Publish Updates** to validate all records, save to YAML, and rebuild the index.

### REST API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/query` | Match a question → answer |
| `GET` | `/api/records` | List all records |
| `POST` | `/api/records` | Create a record |
| `PUT` | `/api/records/<id>` | Update a record |
| `DELETE` | `/api/records/<id>` | Delete a record |
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

---

## Documentation

- [Implementation guide](docs/implementation.md)
- [Configuration reference](docs/configuration.md)
- [Knowledge base schema](docs/schema.md)
- [Deployment options](docs/deployment.md)
- [Contributing guide](docs/contributing.md)

---

## License

MIT
