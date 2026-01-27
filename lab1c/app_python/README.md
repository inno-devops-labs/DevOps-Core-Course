# DevOps Info Service (FastAPI)

## Overview
Web service returning system info about the machine it runs on, plus a simple health check.

## Prerequisites
- Python 3.11+
- pip
- (Optional) venv tool

## Installation
### Windows
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Running the Application
```bash
python app.py
```

Custom cfg examples:
```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
```

FastAPI docs:
- `http://localhost:port/docs`

## API Endpoints
- `GET /` - Service and system information
- `GET /health` - Health check

## Configuration
| Variable | Default | Description |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Bind address for the server |
| `PORT` | `5000` | Port to listen on |
| `DEBUG` | `False` | Enable auto-reload |
