# DevOps Info Service

[![Python CI](https://github.com/kolsmer/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=master)](https://github.com/kolsmer/DevOps-Core-Course/actions/workflows/python-ci.yml)

A web service that provides detailed information about itself and its runtime environment. Built with FastAPI, this service exposes system information, health status, and runtime metrics through REST API endpoints.

## Overview

The DevOps Info Service is a production-ready Python web application designed to demonstrate best practices in web development and system introspection. It serves as a foundation for monitoring and observability solutions throughout the DevOps course.

**Features:**
- Comprehensive system information reporting
- Health check endpoint for monitoring
- RESTful API design
- Environment variable configuration
- Professional logging and error handling
- Clean, well-documented code

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation

1. **Clone or download the project:**
```bash
cd app_python
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

## Running the Application

### Default Configuration
Start the service on `0.0.0.0:8000`:
```bash
python app.py
```

### Custom Configuration
Use environment variables to configure the service:

```bash
# Custom port
PORT=8080 python app.py

# Custom host (localhost only)
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=true python app.py
```

### Using Uvicorn Directly
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### GET /
Returns comprehensive service and system information.

**Response Example:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "ramil-Vivobook",
    "platform": "Linux",
    "platform_version": "6.14.0-37-generic",
    "architecture": "x86_64",
    "cpu_count": 12,
    "python_version": "3.12.3"
  },
  "runtime": {
    "uptime_seconds": 3982,
    "uptime_human": "1 hour, 6 minutes",
    "current_time": "2026-01-27T12:20:08.134918+00:00Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.5.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check"
    },
    {
      "path": "/visits",
      "method": "GET",
      "description": "Visits counter"
    }
  ]
}
```

**Test with curl:**
```bash
curl http://localhost:8000/
curl http://localhost:8000/ | jq  # Pretty print with jq
```

### GET /health
Health check endpoint for monitoring and orchestration (e.g., Kubernetes probes).

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T10:30:00.000000Z",
  "uptime_seconds": 3600
}
```

**Test with curl:**
```bash
curl http://localhost:8000/health
```

**Monitoring Usage:**
```bash
# Check health continuously
while true; do
  curl -s http://localhost:8000/health | jq .
  sleep 5
done
```

### GET /visits
Returns current persistent visits counter value.

```json
{
  "visits": 42,
  "file": "/data/visits"
}
```

**Test with curl:**
```bash
curl http://localhost:8000/visits
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server binding address |
| `PORT` | `8000` | Server port |
| `DEBUG` | `False` | Enable debug mode |
| `VISITS_FILE` | `/data/visits` | File path for persistent visits counter |

### Local Docker Compose Persistence Test

```bash
cd app_python
mkdir -p data
docker compose up -d --build

# Generate visits
curl -s http://localhost:8000/
curl -s http://localhost:8000/
curl -s http://localhost:8000/visits

# Counter persisted in host file
cat data/visits

# Restart container and verify persistence
docker compose restart
curl -s http://localhost:8000/visits
```

### Example Configurations

**Development:**
```bash
DEBUG=true HOST=127.0.0.1 PORT=5000 python app.py
```

**Production:**
```bash
HOST=0.0.0.0 PORT=8000 python app.py
```

**Docker:**
```bash
docker run -p 8000:8000 -e HOST=0.0.0.0 -e PORT=8000 devops-service
```

## Code Structure

```
app_python/
├── app.py              # Main application with FastAPI endpoints
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore configuration
├── README.md          # This file
├── tests/             # Test modules
│   └── __init__.py
└── docs/              # Documentation
    ├── LAB01.md       # Lab submission
    └── screenshots/   # Evidence screenshots
```

## Best Practices Implemented

1. **Clean Code Organization**
   - Clear function names and docstrings
   - Logical import grouping
   - Comments only where necessary
   - PEP 8 compliant

2. **Error Handling**
   - Global exception handlers for 404 and 500 errors
   - Meaningful error messages
   - Proper HTTP status codes

3. **Logging**
   - Configured logging system
   - Info level logs for important events
   - Error tracking with stack traces

4. **Configuration**
   - Environment variable support
   - Sensible defaults
   - Easy customization

5. **Dependencies**
   - Pinned exact versions in requirements.txt
   - Minimal dependencies (FastAPI + Uvicorn only)
   - Production-ready packages

## Testing

### Automated Testing (pytest)

```bash
pytest
```

### Manual Testing

```bash
# Start server
python app.py

# In another terminal:

# Test main endpoint
curl http://localhost:8000/

# Test with formatting
curl http://localhost:8000/ | jq

# Test health endpoint
curl http://localhost:8000/health

# Test with custom headers
curl -H "Custom-Header: test" http://localhost:8000/

# Test 404 error
curl http://localhost:8000/nonexistent
```

### Using HTTPie (alternative to curl)

```bash
http GET localhost:8000/
http GET localhost:8000/health
http --pretty=all GET localhost:8000/
```

## Troubleshooting

**Port already in use:**
```bash
# Use a different port
PORT=9000 python app.py

# Or kill process on port 8000 (Linux/Mac)
lsof -ti:8000 | xargs kill -9
```

**Import errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Connection refused:**
- Ensure the service is running
- Check the HOST and PORT configuration
- Verify firewall settings

## Development

### Adding New Endpoints

```python
@app.get("/custom")
async def custom_endpoint(request: Request):
    """Your endpoint description."""
    return JSONResponse({
        "message": "Your response here"
    })
```

### Running with Auto-reload

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### Interactive API Documentation

FastAPI provides interactive documentation at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Docker

### Building the Image

```bash
docker build -t kolsmer/devops-app:1.0 .
```

### Running the Container

```bash
docker run -d -p 8000:8000 --name devops-app kolsmer/devops-app:1.0
```

### Testing the Containerized App

```bash
curl http://localhost:8000/
curl http://localhost:8000/health
```

### Pulling from Docker Hub

```bash
docker pull kolsmer/devops-app:1.0
docker run -d -p 8000:8000 kolsmer/devops-app:1.0
```

### Stopping the Container

```bash
docker stop devops-app
docker rm devops-app
```

For detailed Docker implementation, see [docs/LAB02.md](docs/LAB02.md).


