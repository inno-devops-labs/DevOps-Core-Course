# DevOps Info Service (Lab 01)

## Overview
A small web service that reports service metadata, system information, runtime info, and request details.

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
cd app_python
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows (PowerShell)
# .\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Running the Application
```bash
python app.py
```

Custom config:
```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true python app.py
```

## API Endpoints
- `GET /` — service + system + runtime + request info
- `GET /health` — health check

## Configuration
| Variable | Default | Description |
|---|---:|---|
| HOST | 0.0.0.0 | Bind address |
| PORT | 5000 | Port |
| DEBUG | False | Flask debug logging & mode |
