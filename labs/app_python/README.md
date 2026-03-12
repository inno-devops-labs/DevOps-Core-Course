# DevOps Info Service

A Python Flask web application that reports system and runtime information.

## Endpoints

- `GET /` — Service and system information (JSON)
- `GET /health` — Health check

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

## Run with Docker

```bash
docker build -t devops-info-service .
docker run -p 8000:8000 devops-info-service
```

## Logging

The app outputs structured JSON logs to stdout. Every HTTP request logs two entries: incoming request and response with status code.

Example:
```json
{"timestamp": "2026-03-12T11:14:28+00:00", "level": "INFO", "message": "Request completed", "method": "GET", "path": "/health", "status_code": 200, "client_ip": "172.0.0.1"}
```
