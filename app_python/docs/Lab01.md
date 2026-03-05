# LAB01 — DevOps Info Service (Python / Flask)

## 1. Framework Selection

**Chosen framework:** Flask

Flask was selected for this lab because it allows building a production-ready
HTTP service with minimal boilerplate and dependencies. This is especially
important for an introductory DevOps lab, where the focus is on understanding
service behavior, configuration, and observability rather than framework
complexity.

### Comparison with Alternatives

| Framework | Advantages | Disadvantages | Suitability |
|---------|------------|---------------|-------------|
| Flask | Lightweight, simple, minimal dependencies | Fewer built-in features | **Best fit** |
| FastAPI | Modern, async, automatic OpenAPI docs | Requires ASGI server, more concepts | Good but unnecessary |
| Django | Full-featured, ORM, admin panel | Heavy and complex for small service | Overkill |

Flask provides the fastest path from idea to a working service while keeping
full control over runtime behavior.

---

## 2. Best Practices Applied

### Clean Code Organization
- Clear separation of configuration, helpers, and route handlers
- Constants used for service metadata and environment configuration
- Small, well-named helper functions (`get_uptime`, `get_system_info`)

### Configuration via Environment Variables
- `HOST`, `PORT`, and `DEBUG` are configurable
- Defaults allow running the service without any configuration
- Enables easy reuse in Docker and Kubernetes environments

### Logging
- Standard Python `logging` module is used
- Log level depends on `DEBUG` flag
- Incoming requests are logged (method, path, user-agent, client IP)

Example:
```python
logging.basicConfig(level=logging.INFO)
logger.info("Application starting")
```

### Error Handling
- Custom JSON responses for HTTP 404 and 500 errors
- Ensures consistent API behavior even on failures
- Internal errors are logged with stack traces

---

## 3. API Documentation

### GET `/`
Returns information about the service, system, runtime, request context,
and available endpoints.

Example request:
```bash
curl -s http://127.0.0.1:5000/ | python -m json.tool
```

### GET `/health`
Simple health-check endpoint used for monitoring and container probes.

Example request:
```bash
curl -s http://127.0.0.1:5000/health | python -m json.tool
```

---

## 4. Testing Evidence

The following screenshots are included in `docs/screenshots/`:

1. **01-main-endpoint.png**
   ![alt text](screenshots/01-main-endpoint.png)
   Full JSON output from the main endpoint (`GET /`)

2. **02-health-check.png**  
   ![alt text](screenshots/02-health-check.png)
   Health check response from `GET /health`

3. **03-formatted-output.png**  
   Pretty-printed JSON output using `python -m json.tool`

These screenshots confirm that all required endpoints work correctly.

---

## 5. Challenges & Solutions

### Determining Client IP
- Problem: `remote_addr` may be incorrect behind reverse proxies
- Solution: Prefer `X-Forwarded-For` header when present

### Correct Uptime Calculation
- Problem: Uptime must be consistent across requests
- Solution: Store application start time once at process startup (UTC)

---

## 6. GitHub Community

Starring repositories is a simple way to support open-source maintainers and
signal useful or high-quality projects. Star counts also improve project
visibility and discovery on GitHub.

Following developers and classmates helps track their work, learn from their
solutions, and simplifies collaboration in team-based and professional
environments.