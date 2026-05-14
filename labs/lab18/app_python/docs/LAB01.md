# Lab 01

## Framework Selection

Choice: FastAPI

Why? FastAPI is designed specifically for building high-performance APIs with Python. It provides automatic data validation and generates interactive documentation (Swagger UI) out of the box.

## Best Practices Applied

### Environment configation

The application avoids hardcoding sensitive or environment-specific values. It uses os.getenv to allow configuration via container environments or .env files.

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

### Logging

Instead of using print() statements, the service implements the standard logging library with configurable levels.

```python
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## API Documentation

### Endpoint: Root Info

Path: /

Method: GET

Response Example:

```json
{
  "service": { "name": "devops-info-service", "version": "1.0.0" },
  "system": { "hostname": "local-machine", "platform": "Linux" },
  "runtime": { "uptime_seconds": 120 }
}
```

### Endpoint: Health Check

Path: /health

Method: GET

Response Example:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T18:30:00Z",
  "uptime_seconds": 120
}
```

### Testing Commands

To test the service via CLI, use curl:

```bash
# Test Root Info
curl http://localhost:5000/

# Test Health Check
curl http://localhost:5000/health
```

### Testing Evidence

![application](screenshots/startup.png?raw=true "Running application")

![health endpoint](screenshots/health.png?raw=true "Health endpoint")

![root endpoint](screenshots/root.png?raw=true "Root info")

### Challenges & Solutions

I forgot how to launch a fastapi application via uicorn without a direct command in the terminal.

Solution:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT,
                log_level='debug' if DEBUG else 'info')
```
