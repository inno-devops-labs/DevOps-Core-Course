# DevOps Info Service

[![Python CI/CD](https://github.com/USERNAME/REPO/actions/workflows/python-ci.yml/badge.svg)](https://github.com/USERNAME/REPO/actions/workflows/python-ci.yml)

A FastAPI-based web service that provides comprehensive information about itself and its runtime environment.

## Overview

The DevOps Info Service is a production-ready web application that exposes system information, runtime metrics, and health status through RESTful API endpoints. It's designed to be containerized and deployed in various environments.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd DevOps-Core-Course
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development dependencies
   ```

## Running the Application

### Basic Usage

```bash
python app.py
```

The service will start on `http://0.0.0.0:5000` by default.

### Custom Configuration

You can configure the application using environment variables:

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=true python app.py
```

### Using Docker

```bash
# Build the image
docker build -t devops-info-service .

# Run the container
docker run -p 5000:5000 devops-info-service

# With custom port
docker run -p 8080:5000 -e PORT=5000 devops-info-service
```

## API Endpoints

### `GET /`

Returns comprehensive service and system information.

**Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "hostname",
    "platform": "Linux",
    "platform_version": "Linux-6.x.x",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.11.x"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2024-01-15T14:30:00.000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### `GET /health`

Health check endpoint for monitoring and orchestration systems.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

### `GET /docs`

Interactive API documentation (Swagger UI).

### `GET /redoc`

Alternative API documentation (ReDoc).

### `GET /openapi.json`

OpenAPI schema in JSON format.

### `GET /visits`

Returns the current persisted visit count.

**Response:**
```json
{
  "visits": 42
}
```

## Persistence (Lab 12)

The service increments a visit counter on each request to `/` and persists it to a file at `DATA_DIR/visits`.

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `DATA_DIR` | `/data` | Directory to store persisted data (visit counter file `visits`) |
| `CONFIG_PATH` | `/config/config.json` | Optional config file path (mounted via ConfigMap in Kubernetes) |

## Testing

### Running Tests

```bash
# Run all tests
pytest app_python/tests/ -v

# Run with coverage report
pytest app_python/tests/ -v --cov=. --cov-report=term-missing

# Run specific test class
pytest app_python/tests/test_app.py::TestRootEndpoint -v

# Run specific test
pytest app_python/tests/test_app.py::TestRootEndpoint::test_root_endpoint_status_code -v
```

### Test Coverage

The test suite includes:
- ✅ Endpoint status code validation
- ✅ JSON response structure validation
- ✅ Data type checking
- ✅ Error handling (404, 405)
- ✅ Utility function testing
- ✅ Performance benchmarks

### Running Linters

```bash
# Flake8 (linting)
flake8 . --count --statistics

# Black (formatting check)
black --check --diff .

# Black (auto-format)
black .
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind to |
| `PORT` | `5000` | Port number to listen on |
| `DEBUG` | `False` | Enable debug mode (auto-reload) |

## Development

### Project Structure

```
app_python/
├── tests/
│   ├── __init__.py
│   └── test_app.py          # Test suite
├── docs/
│   └── LAB03.md             # Lab documentation
├── pytest.ini               # Pytest configuration
└── README.md                # This file

app.py                       # Main application file
requirements.txt             # Production dependencies
requirements-dev.txt         # Development dependencies
Dockerfile                   # Docker configuration
.dockerignore                # Docker ignore patterns
```

### Adding New Endpoints

1. Add the endpoint handler in `app.py`
2. Write tests in `app_python/tests/test_app.py`
3. Update the endpoints list in the root endpoint response
4. Run tests to ensure everything works

## CI/CD

This project uses GitHub Actions for continuous integration:

- **Automated Testing:** Runs on every push and pull request
- **Code Quality:** Linting and formatting checks
- **Security Scanning:** Snyk vulnerability scanning
- **Docker Build:** Automated image building and pushing to Docker Hub
- **Versioning:** Calendar Versioning (CalVer) strategy

See `.github/workflows/python-ci.yml` for the complete CI/CD pipeline configuration.

## License

This project is part of a DevOps course curriculum.

## Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Ensure all tests pass
5. Submit a pull request

