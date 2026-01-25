# devops-info-service

## Overview
`devops-info-service` is a lightweight HTTP service built with **FastAPI** that returns comprehensive runtime and system information. It exposes:
- service metadata (name, version, description, framework),
- system details (hostname, OS/platform, architecture, CPU count, Python version),
- runtime data (uptime, current UTC time),
- request details (client IP, user-agent, method, path),
- a list of available endpoints.

## Prerequisites
- **Python:** 3.10+ (recommended 3.11+)
- **Dependencies:** listed in `requirements.txt`

## Installation

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application
```
python app.py
# Or with custom config
PORT=8080 python app.py
```

## API Endpoints
- `GET /` - Service and system information
- `GET /health` - Health check

## Configuration

The application is configured using environment variables.

| Variable | Default | Description | Example     |
|---------|---------|-------------|-------------|
| `HOST`  | `0.0.0.0` | Host interface to bind the server to | `127.0.0.1` |
| `PORT`  | `8000` | Port the server listens on | `8080`      |