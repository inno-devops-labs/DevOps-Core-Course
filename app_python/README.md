# DevOps Info Service

A FastAPI-based web service that provides system information, runtime metrics, and health monitoring. Built as part of the DevOps course.

## Overview

This service exposes RESTful endpoints that return:
- Service metadata and system information
- Runtime metrics (uptime, current time)
- Request details (client IP, user agent)
- Health check status for monitoring

## Prerequisites

- Python 3.11+ 
- pip

## Installation

```bash
# Navigate to project directory
cd DevOps-Course/lab01/app_python

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

**Default (0.0.0.0:5000):**
```bash
python app.py
```

**Custom configuration:**
```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true PORT=8080 python app.py
```

**Development with auto-reload:**
```bash
uvicorn app:app --reload
```

## API Endpoints

### `GET /`
Returns comprehensive service and system information.

```bash
curl http://localhost:5000/
```

**Response includes:**
- Service metadata (name, version, framework)
- System info (hostname, platform, architecture, CPU count, Python version)
- Runtime metrics (uptime, current time, timezone)
- Request details (client IP, user agent, method, path)
- Available endpoints

### `GET /health`
Health check endpoint for monitoring tools.

```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T07:32:24.854178+00:00",
  "uptime_seconds": 42
}
```

### Interactive Documentation

- **Swagger UI:** http://localhost:5000/docs

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `5000` | Server port number |
| `DEBUG` | `False` | Enable debug mode |

## Testing

```bash
# Test endpoints
curl http://localhost:5000/
curl http://localhost:5000/health

# Pretty-print JSON
curl -s http://localhost:5000/ | python3 -m json.tool
```

## Troubleshooting

**Port already in use:**
```bash
PORT=8080 python app.py
# Or find and kill the process: lsof -i :5000
```

**Module not found:**
```bash
pip install -r requirements.txt
```

## Project Structure

```
app_python/
├── app.py                 # Main application
├── requirements.txt       # Dependencies
├── README.md             # This file
├── tests/                # Unit tests
└── docs/                 # Documentation
    ├── LAB01.md         # Lab report
    └── screenshots/     # Evidence
```

