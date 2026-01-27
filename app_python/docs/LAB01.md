# Lab 1 - DevOps Info Service: Web Application Development

## Framework selection
For this lab, I chose **Flask** as the web framework.
Flask is a lightweight and minimalistic framework that provides full control over request handling and application structure.

I had prior experience working with Flask, which allowed me to focus on the DevOps-related goals of the assignment rather than spending time learning a new framework.

Flask is well-suited for small services and internal tools, which aligns with the purpose of this DevOps Info Service. Its simplicity makes the application easier to understand, maintain, containerize, and monitor in later labs.

## Best Practices Applied
- PEP 8
- Centralized config via env vars
- Structured logging
- Explicit error handlers

## API Documentation
### Request / response examples:
#### 1. Main Endpoint `Get /`

**Request:**
```bash
curl http://localhost:5000 | jq
```

**Response Example:**
```json
{
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    }
  ],
  "request": {
    "client_ip": "127.0.0.1",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/8.7.1"
  },
  "runtime": {
    "current_time": "2026-01-27T12:16:29.586466+00:00",
    "timezone": "UTC",
    "uptime_human": "0 hours, 0 minutes",
    "uptime_seconds": 7
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "x86_64",
    "cpu-count": 8,
    "hostname": "MacBook-Pro-Aliia.local",
    "platform": "Darwin",
    "platform-version": "Darwin Kernel Version 24.6.0: Wed Nov  5 21:30:23 PST 2025; root:xnu-11417.140.69.705.2~1/RELEASE_X86_64",
    "python-version": "3.11.0"
  }
}
```

#### 2. Health check `Get /health`

**Request:**
```bash
curl http://localhost:5000 | jq
```

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T13:44:02.759040+00:00",
  "uptime_seconds": 5260
}
```

## Testing Evidence
### Main Endpoint:
![01-main-endpoint](screenshots/01-main-endpoint.png)
### Health Check:
![02-health-check](screenshots/02-health-check.png)
### Formatted Output:
![03-formatted-output](screenshots/03-formatted-output.png)

## Challenges & Solutions
### Correct Uptime Calculation
**Problem:**
The application is required to report accurate uptime information in seconds and in a human-readable format. A naive implementation based on system uptime or repeated timestamp calculations can lead to inconsistent results, especially after application restarts or during long-running sessions.

**Solution:**
To ensure consistent and deterministic uptime values, the application records a fixed START_TIME at launch using UTC time. Uptime is then calculated as the difference between the current UTC timestamp and this initial start time.
This approach guarantees stable and reproducible uptime values and avoids issues related to local time zones or system clock changes.

## GitHub Community
### Importance of Starring Repositories
Starring repositories on GitHub serves both practical and community purposes. From a personal perspective, stars act as bookmarks that make it easier to return to useful tools and references. From a community perspective, stars provide a visible signal of interest and trust, helping high-quality projects gain visibility and attract contributors.
For open-source maintainers, stars also function as feedback and motivation to continue development.

### Value of Following Developers and Classmates
Following developers on GitHub allows staying informed about their activity, projects, and coding practices. This helps with learning through real-world examples and understanding how others approach problem-solving.
Following classmates supports collaboration within the course by making it easier to discover their work, exchange ideas, and build connections that can be useful in future team-based projects and professional development.