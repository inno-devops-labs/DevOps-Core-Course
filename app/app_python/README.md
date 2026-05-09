# DevOps Info Service (Flask)
[![Python CI/CD](https://github.com/Linktur/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=master)](https://github.com/Linktur/DevOps-Core-Course/actions/workflows/python-ci.yml)

## Overview
A small Flask web service that reports service metadata, system information, runtime details, and request context. It also exposes a health check endpoint and Swagger UI.

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows PowerShell
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Configuration via .env (optional)
Create a `.env` file in `app_python/`:
```env
HOST=0.0.0.0
PORT=5000
DEBUG=false
APP_ENV=dev
LOG_LEVEL=info
APP_CONFIG_PATH=config/config.json
VISITS_FILE_PATH=data/visits
```

## Running the Application
```bash
python app.py
```

With custom configuration:
```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 DEBUG=true python app.py
```

Windows PowerShell:
```powershell
$env:PORT=8080; python app.py
$env:HOST='127.0.0.1'; $env:PORT=3000; $env:DEBUG='true'; python app.py
```

## Docker
Build image (pattern):
```bash
docker build -t linktur/devops-lab2:v1 .
```

Run container (pattern):
```bash
docker run --rm -p 5000:5000 --name devops-lab2 linktur/devops-lab2:v1
```

Pull from Docker Hub (pattern):
```bash
docker pull linktur/devops-lab2:v1
```

## API Endpoints
- `GET /` - Service and system information
- `GET /health` - Health check
- `GET /visits` - Current visits counter
- `GET /swagger.json` - OpenAPI spec
- `GET /docs` - Swagger UI

## Local Quality Checks
Install development dependencies:
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Run linter:
```bash
ruff check .
```

Run unit tests:
```bash
pytest
```

Run tests with coverage threshold (same as CI):
```bash
pytest --cov=. --cov-report=term-missing --cov-fail-under=70
```

## Configuration
| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `5000` | HTTP port |
| `DEBUG` | `False` | Flask debug mode (`true`/`false`) |
| `APP_ENV` | `dev` | Runtime environment name |
| `LOG_LEVEL` | `info` | Logging level exposed via config |
| `APP_CONFIG_PATH` | `config/config.json` | Path to JSON config file |
| `VISITS_FILE_PATH` | `data/visits` | File storing the persistent visits counter |

## Persistent Visits Counter
The root endpoint increments a counter stored in a file. The current value is returned by `GET /visits`.

Local run:
```bash
python app.py
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/visits
cat data/visits
```

Docker Compose with persistent storage:
```bash
docker compose up --build
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/visits
cat ./data/visits
docker compose down
docker compose up
curl http://127.0.0.1:5000/visits
```
