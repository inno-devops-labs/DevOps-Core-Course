# DevOps Info Service

A comprehensive web service that provides detailed information about itself and its runtime environment. Built as part of the DevOps Core Course Lab 1.

## Overview

This service exposes RESTful API endpoints that report system information, runtime metrics, and health status. It serves as a foundation for learning containerization, CI/CD, monitoring, and Kubernetes deployment throughout the DevOps course.

## Prerequisites

- **Python:** 3.11 or higher
- **pip:** Latest version
- **Virtual environment:** Recommended for dependency isolation

## Installation

1. **Navigate to the application directory:**
   ```bash
   cd app_python
   ```

2. **Create and activate a virtual environment:**

   **On Windows:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   **On macOS/Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Default Configuration

Run with default settings (host: 0.0.0.0, port: 5000):

```bash
python app.py
```

### Custom Configuration

Configure using environment variables:

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode (not recommended for production)
DEBUG=true python app.py
```

**On Windows PowerShell:**
```powershell
$env:PORT=8080; python app.py
```

### Using Gunicorn (Production)

For production deployments, use Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

### `GET /`

Returns comprehensive service and system information.

**Example Request:**
```bash
curl http://localhost:5000/
```

**Example Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Windows",
    "platform_version": "10",
    "architecture": "AMD64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "0 hours, 2 minutes",
    "current_time": "2026-01-28T14:30:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.0.1",
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
    }
  ]
}
```

### `GET /health`

Health check endpoint for monitoring and Kubernetes liveness/readiness probes.

**Example Request:**
```bash
curl http://localhost:5000/health
```

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T14:30:00.000000+00:00",
  "uptime_seconds": 120
}
```

**Status Codes:**
- `200 OK` - Service is healthy

## Configuration

The application supports the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host address |
| `PORT` | `5000` | Server port number |
| `DEBUG` | `False` | Enable debug mode (true/false) |

## Project Structure

```
app_python/
├── app.py                    # Main application
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── tests/                   # Unit tests (Lab 3)
│   └── __init__.py
└── docs/                    # Lab documentation
    ├── LAB01.md            # Lab submission
    └── screenshots/        # Evidence screenshots
```

## Testing

### Manual Testing

1. **Start the application:**
   ```bash
   python app.py
   ```

2. **Test main endpoint:**
   ```bash
   curl http://localhost:5000/
   ```

3. **Test health endpoint:**
   ```bash
   curl http://localhost:5000/health
   ```

4. **Test with formatted output:**
   ```bash
   curl http://localhost:5000/ | python -m json.tool
   ```

### Using HTTPie (Alternative)

```bash
# Install HTTPie
pip install httpie

# Test endpoints
http localhost:5000/
http localhost:5000/health
```

## Development

### Code Style

This project follows PEP 8 Python style guidelines. Key practices:

- Use 4 spaces for indentation
- Maximum line length: 79 characters for code, 72 for comments
- Use descriptive variable and function names
- Include docstrings for all functions and classes

### Logging

The application includes structured logging:

```python
# Logs are written to stdout with timestamps
2026-01-28 14:30:00,123 - __main__ - INFO - Starting DevOps Info Service...
2026-01-28 14:30:00,124 - __main__ - INFO - Host: 0.0.0.0, Port: 5000, Debug: False
```

## Troubleshooting

### Port Already in Use

If you get an "Address already in use" error:

```bash
# Use a different port
PORT=8080 python app.py
```

### Module Not Found

Ensure you've activated the virtual environment and installed dependencies:

```bash
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
```

### Permission Denied (Linux/macOS)

If you get permission errors on ports < 1024:

```bash
# Use a port >= 1024
PORT=5000 python app.py
```

## Future Enhancements

This service will evolve throughout the course:

- **Lab 2:** Docker containerization with multi-stage builds
- **Lab 3:** Unit tests and CI/CD pipeline with GitHub Actions
- **Lab 8:** Prometheus `/metrics` endpoint for monitoring
- **Lab 9:** Kubernetes deployment with health probes
- **Lab 12:** Persistent visit counter with file storage

## License

Educational project for DevOps Core Course.

## Author

Created as part of Lab 1 - DevOps Engineering: Core Practices
