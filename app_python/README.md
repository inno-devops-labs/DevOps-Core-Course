# DevOps Info Service (Python / FastAPI)

## Overview

DevOps Info Service is a small web API that reports:
- Service metadata
- System information
- Runtime health and uptime
- Basic request details

It is designed as a foundation for later labs (Docker, CI/CD, monitoring, and Kubernetes).

## Prerequisites

- Python 3.11 or newer
- `pip` (usually bundled with Python)

## Installation

Create a virtual environment and install dependencies:

```bash
python -m venv venv
```

Activate it:

```bash
# Linux / macOS
source venv/bin/activate

# Windows PowerShell
venv\Scripts\Activate.ps1
```

Install requirements:

```bash
pip install -r requirements.txt
```

## Running the Application

You can run via `python app.py` (it starts Uvicorn internally):

```bash
python app.py
```

Or run Uvicorn directly:

```bash
# From the app_python directory
uvicorn app:app --host 0.0.0.0 --port 5000

# From the repository root
uvicorn app_python.app:app --host 0.0.0.0 --port 5000
```

Run with custom configuration:

```bash
# Bash-style
PORT=8080 python app.py

# Windows PowerShell
$env:PORT=8080
python app.py
```

Try the endpoints:

```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/health
```

## API Endpoints

- `GET /` - Service and system information
- `GET /health` - Health check for probes and monitoring

## Configuration

The service is configured through environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Host interface to bind |
| `PORT` | `5000` | Port to listen on |
| `DEBUG` | `false` | Enable debug-level logging |
