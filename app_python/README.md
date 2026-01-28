# DevOps Info Service

## Overview
This service reports:
- Service metadata (name, version, framework)
- System data (hostname, operating system, cpu, python version)
- Runtime data (uptime and current UTC time)
- Request metadata (IP, user agent, method, path)

## Prerequisites
- Python 3.11+

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
```

## API Endpoints
- `GET /` - Service and system information
- `GET /health` - Health check

## Configuration
`HOST`  -  Interface to bind (0.0.0.0 by default)

`PORT` - Port to listen on (5000 by default)

`DEBUG` - Enable Flask debug logging (False by default)

