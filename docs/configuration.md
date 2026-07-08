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

## `editor` section

```yaml
editor:
  require_auth: false
```

| Key | Default | Description |
|---|---|---|
| `require_auth` | `false` | When `true`, the application expects your auth middleware to protect the `/editor` route before the request reaches Flask. QAKey does not implement authentication itself. |

---

## Environment variable

Set `QAKEY_CONFIG` to load a configuration file from an alternate path:

```bash
QAKEY_CONFIG=/etc/qakey/prod.yaml python app.py
```

This is useful for managing separate configurations for development, staging, and production environments.
