# DevOps Info Service (Python)

Lab 1 Python web application that exposes system info and a health check endpoint.

## Overview
This service reports:
- Service metadata (name/version/framework)
- System data (hostname, OS, CPU, Python version)
- Runtime data (uptime and current UTC time)
- Request metadata (client IP, user agent, method, path)

## Prerequisites
- Python 3.11+ recommended

## Installation
```bash
cd app_python
python -m venv venv
source venv/bin/activate # or source `venv/bin/activate.fish` if you using fish instead of bash/sh.
pip install -r requirements.txt
```

## Running the Application
```bash
python app.py

# Or with custom config
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=True python app.py
```

## API Endpoints
- `GET /` - Service and system information
- `GET /health` - Health check

## Configuration
| Env Var | Default | Description |
|---------|---------|-------------|
| `HOST`  | `0.0.0.0` | Interface to bind |
| `PORT`  | `5000` | Port to listen on |
| `DEBUG` | `False` | Enable Flask debug logging |

## Example Requests
```bash
curl -s http://localhost:5000/ | jq .
curl -s http://localhost:5000/health | jq .
```
