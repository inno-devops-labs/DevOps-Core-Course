# DevOps Info Service

## Overview
A simple Python web service that returns service info, system information, runtime uptime, and request details.

## Prerequisites
- Python 3.10+ (recommended: latest available in your environment)
- pip + virtualenv

## Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Running the Application
```bash
python3 app.py
```
Custom config:
```bash
PORT=8080 python3 app.py
# or
HOST=127.0.0.1 PORT=3000 DEBUG=true python3 app.py
```
Production-like run (WSGI):
```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

## API Endpoints
- GET `/` — Service and system information
- GET `/health` — Health check

## Configuration
| Variable            | Default                    | Description         |
| ------------------- | -------------------------- | ------------------- |
| HOST                | 0.0.0.0                    | Bind address        |
| PORT                | 5000                       | Listen port         |
| DEBUG               | false                      | Flask debug mode    |
| LOG_LEVEL           | INFO                       | Logging level       |
| SERVICE_NAME        | devops-info-service        | Service name        |
| SERVICE_VERSION     | 1.0.0                      | Service version     |
| SERVICE_DESCRIPTION | DevOps course info service | Service description |

