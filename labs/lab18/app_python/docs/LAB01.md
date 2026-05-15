# LAB01 — DevOps Info Service

## Framework Selection
For this lab, FastAPI was chosen as the web framework due to its modern design,
high performance, and built-in support for OpenAPI documentation. This makes it a suitable choice for building production-ready services and for future DevOps labs.  

| Framework | Advantages | Disadvantages |
|----------|------------|---------------|
| Flask | Simple and lightweight | No built-in API docs |
| FastAPI | Async, automatic docs, fast | Slight learning curve |
| Django | Full-featured framework | Overkill for small services |

---

## Best Practices Applied
The following best practices were applied during development:

- Clear and simple project structure
- Environment-based configuration using `HOST` and `PORT`
- Separation of logic into helper functions
- Use of UTC timezone for all runtime timestamps
- Dependency management using `requirements.txt`
- Virtual environment usage
- Handling of invalid endpoints using a custom 404 handler

These practices improve readability, portability, and reliability of the application.

---

## API Documentation

### Main Endpoint — `GET /`
Returns detailed information about the service, system, runtime state, request metadata, and available endpoints.

Example request:
```bash
curl http://localhost:5000/
```
The response includes:
- Service metadata (name, version, framework)
- System information (hostname, OS, CPU, Python version)
- Runtime information (uptime, current UTC time)
- Request details (client IP, user agent, HTTP method)
- List of available endpoints

---

### Health Check — `GET /health`

Returns the current health status of the application and uptime in seconds.

Example request:
```bash
curl http://localhost:5000/health
```
---

## Testing Evidence

To confirm correct application behavior, the following screenshots were taken:

- `01-main-endpoint.png` — response from the main endpoint (`GET /`)
- `02-health-check.png` — response from the health check endpoint (`GET /health`)
- `03-formatted-output.png` — formatted JSON output in the terminal

All screenshots are located in the `docs/screenshots` directory.

---

## Challenges & Solutions

One of the challenges encountered was handling requests to non-existent endpoints.  
This was solved by implementing a custom 404 error handler that returns a clear JSON response instead of a default HTML error page.

---

## GitHub Community

Starring repositories on GitHub helps support open-source maintainers and makes it easier to keep track of useful projects.  
Following developers allows learning from their work, staying updated on new technologies, and building professional connections within the developer community.
