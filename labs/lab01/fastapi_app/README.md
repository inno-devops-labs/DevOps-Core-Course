# LAB01

---

## Configuration

Both services support the following environment variables:

- `HOST` — default `0.0.0.0`
- `PORT` — default FastAPI `8000`, Go `8080`
- `DEBUG` — FastAPI debug toggle — default `false`
- `SERVICE_NAME` — service name (default `devops-info-service` or `devops-info-service-go`)
- `SERVICE_VERSION` — default `1.0.0`
- `SERVICE_DESCRIPTION` — human description

## How to run

Prerequisites:

- Python 3.11+ (for the FastAPI app) or Docker
- Go 1.20+ (for building/running the Go app) or Docker

FastAPI (Python) — run locally:

1. Create virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r DevOps-Core-Course/labs/lab01/fastapi_app/requirements.txt
```

2. Run:

```bash
cd DevOps-Core-Course/labs/lab01/fastapi_app
uvicorn main:app --host 0.0.0.0 --port 8000
```

3. Endpoints:
   - `GET http://0.0.0.0:8000/`
   - `GET http://0.0.0.0:8000/health`

FastAPI (Docker):

- Build:
  - `docker build -t devops-info-fastapi DevOps-Core-Course/labs/lab01/fastapi_app`
- Run:
  - `docker run -p 8000:8000 devops-info-fastapi`

Go app — run locally:

1. Build:

```bash
cd DevOps-Core-Course/labs/lab01/go_app
go build -o devops-info-service-go main.go
```

2. Run:
   - `./devops-info-service-go`
   - By default it listens at `0.0.0.0:8080`
3. Endpoints:
   - `GET http://0.0.0.0:8080/`
   - `GET http://0.0.0.0:8080/health`

Go app (Docker):

- Build:
  - `docker build -t devops-info-go DevOps-Core-Course/labs/lab01/go_app`
- Run:
  - `docker run -p 8080:8080 devops-info-go`
