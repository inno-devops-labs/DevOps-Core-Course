# DevOps Info Service

A Python Flask web application that reports system and runtime information.

## Endpoints

- `GET /` — Service and system information (JSON), increments visit counter
- `GET /visits` — Returns current visit count
- `GET /health` — Health check
- `GET /metrics` — Prometheus metrics

## Visit Counter

The app tracks how many times the root endpoint `/` is accessed. The counter is stored in a file (default: `/data/visits`) so it survives container restarts.

Set the file path with the `VISITS_FILE` environment variable.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

## Run with Docker Compose

```bash
docker compose up -d
```

The compose file mounts `./data` to `/data` inside the container, so the visits counter persists across restarts.

To test persistence:
```bash
# Hit the root endpoint a few times
curl http://localhost:8000/
curl http://localhost:8000/visits

# Restart the container
docker compose restart

# Counter should continue from last value
curl http://localhost:8000/visits
```

## Run with Docker

```bash
docker build -t devops-info-service .
docker run -p 8000:8000 -v $(pwd)/data:/data devops-info-service
```

## Logging

The app outputs structured JSON logs to stdout. Every HTTP request logs two entries: incoming request and response with status code.

Example:
```json
{"timestamp": "2026-03-12T11:14:28+00:00", "level": "INFO", "message": "Request completed", "method": "GET", "path": "/health", "status_code": 200, "client_ip": "172.0.0.1"}
```
