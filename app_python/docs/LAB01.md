# Lab 01 - Python Implementation

Python implementation of the DevOps Info Service using Flask framework.

## Framework Selection

### Choice: Flask

**Why Flask?**
- Lightweight and simple
- Easy to learn and understand
- Flexible project structure
- Industry standard
- Perfect for microservices

**Comparison:**

| Feature | Flask | FastAPI | Django |
|---------|-------|---------|--------|
| Learning Curve | Easy | Moderate | Steep |
| Performance | Good | Excellent | Good |
| Flexibility | High | High | Low |
| Size | Minimal | Small | Large |
| Best For | APIs, Microservices | High-performance APIs | Full-stack apps |

## Best Practices

1. **Clean Code**: PEP 8 compliant, clear function names, logical imports
2. **Environment Variables**: Configurable via `HOST`, `PORT`, `DEBUG`
3. **Error Handling**: Proper error handling with JSON responses
4. **Dependencies**: Pinned versions in `requirements.txt`
5. **Git Ignore**: Excludes cache, venv, IDE files

## API Documentation

### `GET /`
Returns service and system information.

**Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "framework": "Flask"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Darwin",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 1234.56,
    "uptime_human": "0 hours, 20 minutes, 34 seconds"
  }
}
```

### `GET /health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-31T17:30:00.000Z",
  "uptime_seconds": 1234.56
}
```

## Testing

Screenshots available in `docs/screenshots/`:
1. Main endpoint response
2. Health check response
3. Formatted output with jq

**Example:**
```bash
# Start application
python app.py

# Test endpoints
curl http://localhost:5001/ | jq
curl http://localhost:5001/health | jq
```

## Key Features

1. **Uptime Formatting**: Human-readable format with proper pluralization
2. **Timestamp Format**: ISO 8601 with UTC timezone
3. **Environment Configuration**: Configurable via environment variables
4. **Error Handling**: Comprehensive error handling with logging
5. **Logging**: Configured logging for debugging and monitoring

## Challenges & Solutions

### Uptime Formatting
Created `format_uptime()` function that calculates hours, minutes, seconds with proper pluralization.

### Timestamp Format
Used `datetime.now(timezone.utc).isoformat()` with `.000Z` suffix for consistency.

### Environment Variables
Used `os.getenv()` with sensible defaults for configuration.

## GitHub Community

**Actions Completed:**
- ✅ Starred the course repository
- ✅ Starred the simple-container-com/api repository
- ✅ Followed professor and TAs on GitHub
- ✅ Followed at least 3 classmates on GitHub

**Why it matters:**
- Bookmarking and discovery of useful projects
- Community signal and project visibility
- Encouragement for maintainers
- Professional development and networking
