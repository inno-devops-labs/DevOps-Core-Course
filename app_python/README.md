# app_python

Minimal FastAPI service for DevOps Lab 2 (Docker Containerization).

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 5000
```

- http://localhost:5000/
- http://localhost:5000/health

## Docker

### Build

From `app_python/`:

```bash
docker build -t devops-course-lab2:local .
```

### Run

```bash
docker run --rm -p 5000:5000 devops-course-lab2:local
```

### Pull (Docker Hub)

Replace `<dockerhub-username>` with your username:

```bash
docker pull <dockerhub-username>/devops-course-lab2:latest
docker run --rm -p 5000:5000 <dockerhub-username>/devops-course-lab2:latest
```
