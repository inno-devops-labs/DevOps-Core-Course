# DevOps Info Service (Python)

## Overview
Simple Flask web service that reports service metadata, system details, runtime uptime, and request info. Includes a `/health` endpoint for liveness probes.

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application
```bash
python app.py
# Custom configuration
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 DEBUG=true python app.py
```

## API Endpoints
- `GET /` — Service, system, runtime, request info, and endpoint list.
- `GET /health` — Health status and uptime (HTTP 200).

## Configuration
Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST`   | `0.0.0.0` | Bind address |
| `PORT`   | `8080`  | Listening port |
| `DEBUG`  | `False` | Enable Flask debug mode |

## Notes
- Logging is configured at startup; noisy werkzeug logs are suppressed to WARNING.
- Error handlers return JSON for 404 and 500.
