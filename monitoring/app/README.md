# DevOps Info Service

A lightweight Python HTTP server that exposes system info, health checks, visit counting, and Prometheus metrics.

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Application info (name, hostname, visit count). Increments the persistent visits counter. |
| `GET /visits` | Returns the current visit count without incrementing. |
| `GET /health` | Health check — returns `{"status": "healthy", "uptime_seconds": ...}` |
| `GET /metrics` | Prometheus metrics in OpenMetrics format |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `devops-app` | Application name returned by `/` |
| `APP_PORT` | `8000` | Port the server listens on |
| `DATA_DIR` | `/data` | Directory for persistent data (visits counter file) |

## Persistent Visits Counter

The application tracks how many times the root endpoint (`/`) has been accessed:

- Counter is stored in `$DATA_DIR/visits` as a plain-text integer.
- On each `GET /` request the counter is incremented atomically (file lock + atomic rename).
- On startup the counter is read from the file; if the file is missing, it starts at 0.
- The `/visits` endpoint returns the current value without incrementing.

## Running Locally

```bash
pip install -r requirements.txt
DATA_DIR=./data python app.py
```

## Running with Docker Compose

```bash
cd monitoring
docker compose up --build -d

# Access the app
curl http://localhost:8000/
curl http://localhost:8000/visits

# Verify persistence across restarts
docker compose restart app-python
curl http://localhost:8000/visits   # counter preserved
```

## Docker Compose Volume

The `docker-compose.yml` mounts a named volume at `/data` so the visits counter survives container restarts:

```yaml
volumes:
  - app-python-data:/data
```
