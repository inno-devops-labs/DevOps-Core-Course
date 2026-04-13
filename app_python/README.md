# app_python

Minimal FastAPI service for the DevOps course labs.

## Features

- `GET /` returns service information and increments the visits counter
- `GET /visits` returns the current visits counter
- `GET /health` returns health status
- `GET /metrics` returns Prometheus metrics

The visits counter is stored in a file. By default, the application uses `/data/visits`.
You can override this path with the `VISITS_FILE` environment variable.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
VISITS_FILE=./data/visits uvicorn app:app --host 0.0.0.0 --port 5000
```

Test locally:

```bash
curl http://localhost:5000/
curl http://localhost:5000/
curl http://localhost:5000/visits
cat ./data/visits
```

## Docker

### Build

From `app_python/`:

```bash
docker build -t devops-course-lab12:local .
```

### Run

```bash
docker run --rm -p 5000:5000 -e VISITS_FILE=/data/visits -v $(pwd)/data:/data devops-course-lab12:local
```

### Docker Compose

From the repository root:

```bash
docker compose up -d app
curl http://localhost:8000/
curl http://localhost:8000/visits
cat ./data/visits
```

Restart test:

```bash
docker compose restart app
curl http://localhost:8000/visits
cat ./data/visits
```
