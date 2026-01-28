# DevOps Info Service

## Overview

Lightweight web service providing system information, runtime status, and health checks. Foundation for comprehensive DevOps monitoring throughout the course.

## Prerequisites

* Python 3.11+
* pip
* git

## Installation

```
python3.11 -m venv venv
source venv/bin/activate      # Linux/Mac
pip install -r requirements.txt
```

## Running the Application

```
python app.py                    # Default: http://0.0.0.0:5000
PORT=8080 python app.py          # Custom port
HOST=127.0.0.1 PORT=3000 python app.py  # Specific host/port
DEBUG=true python app.py         # Debug mode (auto-reload)

```

## API Endpoints

| Endpoint    | Method | Description                          |
| ----------- | ------ | ------------------------------------ |
| `/`       | GET    | Service, system, runtime information |
| `/health` | GET    | Health status for monitoring         |

```
curl http://localhost:5000/
curl http://localhost:5000/health
```

## Configuration

Environment variables for flexible deployment:

| Variable  | Default     | Description                   |
| --------- | ----------- | ----------------------------- |
| `HOST`  | `0.0.0.0` | Bind address                  |
| `PORT`  | `5000`    | TCP port                      |
| `DEBUG` | `False`   | Debug mode (development only) |

**Example** :

```
export HOST=0.0.0.0
export PORT=8080
export DEBUG=true
python app.py

```
