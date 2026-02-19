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
