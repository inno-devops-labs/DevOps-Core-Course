# DevOps Info Service (Python)

## Overview

DevOps Info Service is a simple web application that provides
information about itself and its runtime environment.

It now includes:
- System and runtime information
- Health endpoint
- Prometheus metrics
- Persistent visits counter

## Endpoints

### GET /

Returns service info and increments visit counter.

### GET /health

Health check endpoint.

### GET /visits

Returns current visit count.

Example:
```bash
curl http://127.0.0.1:5000/visits
```

## Docker Compose

Run:
```bash
docker compose up --build
```
Test:
```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/visits
cat ./data/visits
```

Restart:
```bash
docker compose down
docker compose up
```
The counter should persist because volume is mounted.

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| HOST | 0.0.0.0| Server host |
| PORT| 5000| Server port |
| LOG_LEVEL| INFO| Logging level |
| VISITS_FILE| /data/visits| Visits file path |