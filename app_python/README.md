# DevOps Info Service

## Overview

Web service that reports system information and health status. Provides API endpoints for service info, hostname, platform, uptime, and request details.

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```bash
python app.py
```

Default: `http://0.0.0.0:5000`

**Custom config:**

```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
```

## API Endpoints

### `GET /`

Returns service and system information.

```bash
curl http://localhost:5000/
```

### `GET /health`

Health check endpoint.

```bash
curl http://localhost:5000/health
```

## Configuration

| Variable | Default   | Description  |
| -------- | --------- | ------------ |
| `HOST`   | `0.0.0.0` | Host address |
| `PORT`   | `5000`    | Port number  |
| `DEBUG`  | `False`   | Debug mode   |

## Docker

### Build the image

```bash
docker build -t roma3213/info_service:1.0 .
```

### Run a container

```bash
docker run -p 5000:5000 roma3213/info_service:1.0
```

With custom port:

```bash
docker run -p 5000:5000 roma3213/info_service:1.0
```

### Pull from Docker Hub

```bash
docker pull roma3213/info_service:1.0
docker run -p 5000:5000 roma3213/info_service:1.0
```

## Project Structure

```
app_python/
├── app.py              # Main app
├── config.py           # Config
├── routes/             # API routes
├── services/           # Business logic
├── tests/
├── docs/               # Lab docs, screenshots
├── requirements.txt
├── Dockerfile          # Container image
├── .dockerignore
├── .gitignore
└── README.md
```
