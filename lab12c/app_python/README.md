# DevOps Info (lab 12)

FastAPI app with a visit counter in a file (`VISITS_FILE`, default `/data/visits`). `/` increments, `/visits` just reads.

## Run with Docker Compose

```bash
docker compose up --build
```

Hit `http://127.0.0.1:5000/` a bunch, then `/visits`. Restart the stack — counter should pick up where it left off (`./data` is mounted to `/data`).

## Tests

```bash
pip install -r requirements.txt pytest httpx
pytest -q
```

## Kubernetes image

Build and push something like `tsixphoenix/devops-info-python:lab12` and point `image.repository` / `image.tag` in `lab12c/k8s/devops-info/values.yaml` at the same thing.
