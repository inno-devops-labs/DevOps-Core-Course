# DevOps Info Service

## Overview
A lightweight web service, that exposes the system, runtime, and request information.
Used as a foundation for DevOps labs (Docker, CI/CD, monitoring).

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
# Or with custom config
PORT=8080 python app.py
```

## API Endpoints
- `GET /` - Service and system information
- `GET /health` - Health check

## Configuration

| Variable   | Default   | Description        |
| ---------- | --------- | ------------------ |
| `HOST`     | `0.0.0.0` | Bind address       |
| `PORT`     | `5000`    | Server port number |
| `DEBUG`    | `false`   | Debug mode         |

