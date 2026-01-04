# Moscow Time Display - Python Web Application

## Overview

FastAPI web application displaying current Moscow (MSK) timezone. Features a modern, responsive Bootstrap UI that updates on page refresh.

## Features

- Real-time Moscow timezone display
- Responsive Bootstrap 5 UI
- Health check endpoint
- Docker containerization

## Technology Stack

- **Framework**: FastAPI 0.109.0
- **Server**: Uvicorn
- **Templating**: Jinja2
- **Frontend**: Bootstrap 5
- **Python**: 3.11+

## Quick Start

### Using Docker Compose (Recommended)

```bash
docker compose up
```

Access at: <http://localhost:5000>

### Local Development

```bash
cd app_python
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 5000
```

### Docker Only

```bash
docker build -t moscow-time-app .
docker run -p 5000:5000 moscow-time-app
```

## API Endpoints

- **GET /** - Main page displaying Moscow time
- **GET /health** - Health check endpoint

```json
{
  "status": "healthy",
  "service": "moscow-time-app"
}
```

## Testing

1. Visit <http://localhost:5000>
2. Verify Moscow time is displayed
3. Refresh to see time update
4. Check health: `curl http://localhost:5000/health`
