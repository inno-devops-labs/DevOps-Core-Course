# DevOps Info Service

![Python CI/CD](https://github.com/Ravwvil/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)
![Coverage](https://coveralls.io/repos/github/Ravwvil/DevOps-Core-Course/badge.svg?branch=master)

Web service providing system information and health status via REST API.
The root endpoint also persists a visit counter to disk for Kubernetes PVC and Docker volume exercises.

## Requirements

- Python 3.11+
- pip

## Installation

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

## Usage

```bash
python app.py                      # Default: http://0.0.0.0:8000
PORT=3000 python app.py            # Custom port
```

Persistent counter options:

```bash
VISITS_FILE=./data/visits python app.py
CONFIG_PATH=./config/config.json python app.py
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=. --cov-report=term
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service and system information |
| `/visits` | GET | Current persisted visit count |
| `/health` | GET | Health check |
| `/ready` | GET | Readiness check |
| `/metrics` | GET | Prometheus metrics |
| `/docs` | GET | Swagger UI documentation |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Port number |
| `DEBUG` | `false` | Enable auto-reload |
| `APP_NAME` | `devops-info-service` | Service name exposed in responses |
| `APP_ENV` | `development` | Environment label |
| `APP_REGION` | `local` | Example environment metadata |
| `LOG_LEVEL` | `INFO` | Application log level |
| `CONFIG_PATH` | `/config/config.json` | Mounted JSON configuration file |
| `VISITS_FILE` | `./data/visits` locally | File used for the persistent visits counter |

## Project Structure

```
app_python/
├── app.py              # Main application
├── requirements.txt    # Dependencies (incl. test & lint)
├── Dockerfile          # Container definition
├── .dockerignore       # Docker build exclusions
├── README.md
├── tests/
│   ├── __init__.py
│   └── test_app.py     # Unit tests (pytest)
└── docs/
    ├── LAB01.md
    ├── LAB02.md
    └── LAB03.md
```

## Docker

### Build Image Locally

```bash
docker build -t devops-info-service:latest .
```

### Run Container

```bash
docker run -d -p 8000:8000 --name devops-app devops-info-service:latest
```

Access the application at `http://localhost:8000`

### Run with Docker Compose and Persistent Visits

```bash
docker compose up -d
curl http://localhost:8000/
curl http://localhost:8000/visits
docker compose restart
curl http://localhost:8000/visits
cat ./data/visits
```

The compose setup mounts `./data` into the container so the counter survives container restarts.

### Pull from Docker Hub

```bash
docker pull <your-dockerhub-username>/devops-info-service:latest
docker run -d -p 8000:8000 <your-dockerhub-username>/devops-info-service:latest
```

### Useful Commands

```bash
# View container logs
docker logs devops-app

# Stop container
docker stop devops-app

# Remove container
docker rm devops-app

# Check running containers
docker ps
```
