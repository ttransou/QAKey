# QAKey Deployment Guide

## Development server

The built-in Flask development server is suitable for local testing only.

```bash
python app.py
```

---

## Production deployment

### Gunicorn (Linux/macOS)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:app"
```

### Waitress (Windows-compatible)

```bash
pip install waitress
waitress-serve --port=8000 app:app
```

### Environment variables

| Variable | Description |
|---|---|
| `QAKEY_CONFIG` | Path to a custom config file (default: `config.yaml`) |

---

## Docker

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

Build and run:

```bash
docker build -t qakey .
docker run -p 8000:8000 qakey
```

To persist the knowledge base across container restarts, mount the `knowledge/` directory as a volume:

```bash
docker run -p 8000:8000 -v $(pwd)/knowledge:/app/knowledge qakey
```

---

## Reverse proxy (nginx)

```nginx
server {
    listen 80;
    server_name qa.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Deploying to cloud platforms

### Render / Railway / Fly.io

1. Set the start command to `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`.
2. Mount or commit your `knowledge/` directory so the YAML files are available.
3. Set any environment variables (`QAKEY_CONFIG`) in the platform dashboard.

### Azure App Service

1. Create a Python 3.12 App Service.
2. Set the startup command: `gunicorn -w 4 -b 0.0.0.0:8000 app:app`.
3. Deploy via GitHub Actions, Azure DevOps, or `az webapp up`.

---

## Protecting the editor

The `/editor` route should be accessible only to authorised maintainers.
QAKey does not implement authentication itself — use one of the following approaches:

- **Basic Auth via nginx** — add `auth_basic` directives to the `/editor` location block.
- **OAuth proxy** (e.g. oauth2-proxy) — place in front of the application.
- **Azure AD / Entra ID** — configure App Service Authentication.
- **Network restriction** — restrict access to `/editor` by IP range at the proxy or firewall level.

Set `editor.require_auth: true` in `config.yaml` as a documentation flag indicating that authentication is expected. QAKey itself does not enforce it.

---

## Scaling considerations

QAKey holds the knowledge base index in memory. For most controlled Q&A collections
(hundreds to low thousands of records) this is efficient and requires no special
infrastructure. If your knowledge base grows significantly:

- Consider pre-building the TF-IDF index on startup from a persistent cache.
- For very large corpora, replace the built-in engine with a dedicated vector store
  (e.g. FAISS, Qdrant, or Azure AI Search) while keeping the same `QAEngine` interface.
