# DevOps Info Service

A Python web service that reports system information and health status through a simple REST API.

[![Python CI](https://github.com/hikariatama/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab3)](https://github.com/hikariatama/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![Coverage](https://codecov.io/gh/hikariatama/DevOps-Core-Course/branch/lab3/graph/badge.svg?flag=app_python)](https://codecov.io/gh/hikariatama/DevOps-Core-Course)

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
cd app_python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

## Running

```bash
python app.py
```

With custom configuration:

```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true python app.py
```

For production, use gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Testing

Run linting:

```bash
python -m ruff check app.py tests
```

Run unit tests:

```bash
python -m pytest
```

Run unit tests with coverage and threshold:

```bash
python -m pytest --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=70
```

## Docker

Build image locally:

```bash
docker build -t <dockerhub-username>/<image-name>:<tag> .
```

Run container:

```bash
docker run --rm -p <host-port>:5000 --name <container-name> <dockerhub-username>/<image-name>:<tag>
```

Pull from Docker Hub:

```bash
docker pull <dockerhub-username>/<image-name>:<tag>
```

## API Endpoints

### GET /

Returns service info, system details, runtime stats, and request information.

```bash
curl http://localhost:5000/ | python -m json.tool
```

### GET /health

Health check for monitoring and container orchestration.

```bash
curl http://localhost:5000/health
```

## Configuration

| Variable | Default   | Description  |
| -------- | --------- | ------------ |
| `HOST`   | `0.0.0.0` | Host address |
| `PORT`   | `5000`    | Port number  |
| `DEBUG`  | `false`   | Debug mode   |

## Troubleshooting

**Port in use:** Use a different port with `PORT=8080 python app.py`

**Import errors:** Make sure venv is activated and dependencies are installed

**Permission denied:** Use port > 1024 or run with elevated privileges
