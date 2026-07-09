# QAKey Configuration Reference

All configuration lives in `config.yaml` (or the path set by the `QAKEY_CONFIG` environment variable).

---

## Top-level keys

### `app_name` (string)

Display name shown in the navigation bar and browser tab title.

```yaml
app_name: "QAKey"
```

### `app_tagline` (string)

Subtitle shown beneath the application name on the query interface.

```yaml
app_tagline: "Your organization's trusted Q&A knowledge base"
```

### `host` (string, default `"127.0.0.1"`)

The network interface the Flask development server binds to. Set to `"0.0.0.0"` to accept external connections.

### `port` (integer, default `5000`)

TCP port the application listens on.

### `debug` (boolean, default `false`)

Enable Flask debug mode (auto-reload, detailed error pages). **Do not enable in production.**

---

## `knowledge` section

```yaml
knowledge:
  records_path: "knowledge/qa_records.yaml"
  synonyms_path: "knowledge/synonyms.yaml"
```

| Key | Description |
|---|---|
| `records_path` | Path to the YAML file that stores Q&A records. Created automatically if it does not exist. |
| `synonyms_path` | Path to the YAML synonym mapping file. Set to an empty string to disable synonym expansion. |

---

## `matching` section

```yaml
matching:
  confidence_threshold: 0.25
  no_match_message: >
    I could not find an approved answer for that question.
    Please rephrase your question or contact the team directly.
```

| Key | Default | Description |
|---|---|---|
| `confidence_threshold` | `0.25` | Minimum cosine-similarity score (0–1) required to return an answer. Lower values allow more permissive matching; higher values are stricter. |
| `no_match_message` | (see above) | Message shown to the user when no record meets the threshold. |

### Tuning the confidence threshold

| Value | Behaviour |
|---|---|
| `0.1–0.2` | Very permissive — returns an answer for almost any query. Risk of false positives. |
| `0.25–0.4` | Balanced — recommended starting point for most knowledge bases. |
| `0.5–0.7` | Strict — only returns an answer when the query closely matches a record. |
| `0.8+` | Very strict — essentially requires near-exact phrasing. |

---

## `fallback` section

```yaml
fallback:
  enabled: true
  fallback_log_path: "logs/fallback_queries.jsonl"
  no_match_message: >
    I could not find an approved answer for that question.
    Please rephrase your question or contact the appropriate team directly.
  ambiguous_match_message: >
    I found more than one possible approved question.
    Please choose the closest match or rephrase your question.
```

| Key | Description |
|---|---|
| `enabled` | Enables the compact feedback-alert inbox flow when `true`. |
| `fallback_log_path` | Path to the local JSON file used to store unresolved answer feedback alerts. The file is kept intentionally small and can be trimmed by resolving alerts in the Content Editor. |
| `no_match_message` | Controlled message shown when no approved answer is available. |
| `ambiguous_match_message` | Controlled message shown when more than one approved answer is plausible. |

When feedback alerts are enabled, low-confidence or not-helpful answer feedback is recorded as unresolved alerts for the Content Editor rather than being accumulated as a large free-form log.

---

## `editor` section

```yaml
editor:
  require_auth: false
  admin_username: "admin"
  admin_password: ""
```

| Key | Default | Description |
|---|---|---|
| `require_auth` | `false` | When `true`, the built-in editor login gate is enabled for `/editor` and editor APIs. |
| `admin_username` | `admin` | Local editor admin username (override with environment variable in real deployments). |
| `admin_password` | empty | Local editor admin password (must be set when auth is enabled). |

### Editor auth model

QAKey includes a simple built-in admin/password gate for editor access.
This model is intentionally minimal and can be replaced with enterprise auth layers (SSO, AD, OAuth proxy) when needed.

### Editor alert inbox

The Content Editor includes a compact answer-feedback alert inbox. Alerts are loaded from the configured fallback log path and can be marked addressed from the editor UI. This keeps the stored feedback set small and focused on unresolved items only.

---

## Environment variable

Set `QAKEY_CONFIG` to load a configuration file from an alternate path:

```bash
QAKEY_CONFIG=/etc/qakey/prod.yaml python app.py
```

This is useful for managing separate configurations for development, staging, and production environments.

Additional environment overrides:

| Variable | Description |
|---|---|
| `QAKEY_EDITOR_USERNAME` | Overrides `editor.admin_username` |
| `QAKEY_EDITOR_PASSWORD` | Overrides `editor.admin_password` |
| `QAKEY_SECRET_KEY` | Session signing key for editor login session cookies |
