# Lab 1: Web Framework Selection
## Framework Choice: FastAPI
### Justification for Selection
**FastAPI** was chosen for implementing the DevOps Info Service for the following reasons:

1. **Modernity and Performance**:

   - Support for asynchronous operations (async/await)

   - High performance (built on Starlette and Pydantic)

   - Automatic data validation via Pydantic

2. **Automatic Documentation**:

   - Auto-generation of OpenAPI documentation

   - Interactive Swagger UI available at /docs

   - Alternative ReDoc documentation at /redoc

3. **Type Safety and Security**:

   - Built-in data validation

   - Automatic JSON serialization/deserialization

   - Support for Python type hints (including Python 3.12)

4. **Development Simplicity**:

   - Minimal boilerplate code

   - Simple routing

   - Easy dependency integration

5. **Requirement Compliance**:

   - Ideal for API services

   - Support for modern standards

   - Good ecosystem for DevOps practices

### Alternatives and Why They Were Not Chosen:
- **Flask**: Although lightweight and simple, lacks built-in async support and automatic documentation

- **Django**: Too heavy for a simple API service, contains many redundant features

### Technical Implementation Details:
- **Python Version**: 3.12

- **Main Dependencies**: FastAPI, uvicorn, pydantic

- **Development Server**: Uvicorn with hot reload

- **Data Format**: JSON (API standard)

### Benefits for DevOps:
- **Easy Containerization**: Simple to package in Docker

- **Monitoring**: Built-in support for metrics and health checks

- **Scalability**: Asynchronous nature allows handling multiple requests

- **Documentation**: Automatic API specification generation

## Best Practices Applied

### 1. Clean Code Organization
- Clear function and variable naming
- Logical grouping of imports (standard library → third-party → local)
- Separation of concerns (configuration, logging, endpoints)
- PEP 8 style compliance

**Example:**
```python
import os
import platform
import socket
import logging
from datetime import datetime
```
### 2. Error Handling
Global exception handler for unexpected errors

Custom handlers for 404 and validation errors

Consistent JSON error responses

Example:

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred"}
    )
   ```
### 3. Logging
- Uses Python’s built-in logging module

- INFO logs for startup and requests

- ERROR logs for exceptions

- DEBUG logs for health checks when enabled

- **Importance**:
Logging improves observability, supports troubleshooting, and is essential for production systems.

### 4. Dependencies Management
- Exact versions pinned in requirements.txt for reproducibility

Example:

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
```
### 5. Configuration via Environment Variables
- HOST, PORT, and DEBUG configurable without code changes

Example:

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```
- **Importance**:
Enables flexible deployment across development, testing, and production environments.

## API Documentation
### GET /

Returns comprehensive service, system, runtime, and request information.

- **Request**:
```bash
curl http://localhost:5000/
```

- **Response**:
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  }, ...
}
```

### GET /health

- Returns health status for monitoring and Kubernetes probes.

- **Request**:
```bash
curl http://localhost:5000/health
```


- **Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600,
  "service": "devops-info-service",
  "version": "1.0.0"
}
```
- Testing Commands
```bash
python app.py
curl http://localhost:5000/
curl http://localhost:5000/health
```
## Testing Evidence

Screenshots provided in docs/screenshots/:

- 01-main-endpoint.png — Main endpoint showing complete JSON

- 02-health-check.png — Health check response

- 03-formatted-output.png — Pretty-printed output

## Challenges & Solutions
### Challenge 1: Uptime Calculation

Problem: Converting raw seconds into a human-readable format.

Solution: Implemented a helper function that calculates hours and minutes from the service start time.

### Challenge 2: Centralized Error Handling

Problem: Ensuring consistent JSON error responses across the API.

Solution: Implemented global exception handlers and validation error handlers using FastAPI’s built-in mechanisms.

### Challenge 3: Environment-Based Configuration

Problem: Supporting multiple environments without code changes.

Solution: Used environment variables for host, port, and debug mode.

## GitHub Community

Starring repositories helps support maintainers, increases project visibility, and serves as a personal bookmark for useful tools. Following developers enables networking, collaboration, and continuous learning by observing real-world development practices and community activity.