## LAB01 — DevOps Info Service (Python)

### 1. Framework Selection

**Chosen Framework:** Flask

| Criterion              | Flask                           | FastAPI                               | Django                                 |
|------------------------|----------------------------------|----------------------------------------|----------------------------------------|
| Learning curve         | Very beginner-friendly          | Moderate (type hints, async)          | Steeper (full framework)              |
| Use case fit           | Simple APIs and microservices   | High-performance APIs                  | Large, full-featured web apps         |
| Ecosystem / extensions | Mature ecosystem, many examples | Great docs, built-in OpenAPI docs     | Includes ORM, admin, auth, templates  |
| Setup complexity       | Minimal                         | Minimal                                | Higher (project + apps structure)     |
| For this lab           | Ideal for quick REST services   | Slightly more complex than necessary  | Overkill                              |

**Why Flask?**

- The lab only needs two simple HTTP endpoints and JSON responses.
- Flask is lightweight, easy to understand, and perfect for a small service that will grow over time.
- There is a lot of learning material and community support, which is helpful for beginners.

### 2. Best Practices Applied

- **Clean Code Organization**
  - Clear function names such as `get_system_info()`, `get_uptime()`, and `get_request_info()`.
  - Configuration values (`HOST`, `PORT`, `DEBUG`) are defined at the top of `app.py`.
  - A `main()` function is used as the entrypoint to keep `if __name__ == "__main__":` minimal.

- **PEP 8 Compliance**
  - Imports are grouped (standard library first, then third-party).
  - Snake_case is used for function and variable names.
  - Line lengths and spacing follow PEP 8 conventions.

- **Error Handling**
  - Custom handlers for `404` and `500` errors return JSON responses:
    - `404` includes an error message and the invalid path.
    - `500` returns a generic error message without leaking internals.

- **Logging**
  - Configured via `logging.basicConfig` with timestamp, logger name, level, and message.
  - Logs when the application starts and when requests to `/` and `/health` are handled.
  - Errors and 500s are logged with stack traces for easier debugging.

### 3. API Documentation

#### `GET /`

- **Description:** Returns service, system, runtime, and request information, plus a list of available endpoints.
- **Example Request:**

```bash
curl http://localhost:5000/
```

- **Example Response (truncated):**

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
    "platform": "Linux",
    "platform_version": "Ubuntu 24.04",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.11.0"
  },
  "runtime": {
    "uptime_seconds": 12,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-01-27T14:30:00.000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    { "path": "/", "method": "GET", "description": "Service information" },
    { "path": "/health", "method": "GET", "description": "Health check" }
  ]
}
```

#### `GET /health`

- **Description:** Simple health check used for readiness/liveness probes.
- **Example Request:**

```bash
curl http://localhost:5000/health
```

- **Example Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T14:30:00.000Z",
  "uptime_seconds": 42
}
```

### 4. Testing Evidence

**Manual Testing Commands**

From the `app_python` directory:

```bash
python app.py

# In another terminal
curl http://localhost:5000/ | jq
curl http://localhost:5000/health | jq
```

- `curl` fetches the JSON responses.
- `jq` pretty-prints the JSON output for easier reading.

**Screenshots (to be added by you):**

Place the following screenshots in `app_python/docs/screenshots/`:

- `01-main-endpoint.png` — Browser or terminal showing the full JSON from `GET /`.
- `02-health-check.png` — Response from `GET /health`.
- `03-formatted-output.png` — Pretty-printed JSON output (e.g., using `jq` or browser dev tools).

### 5. Challenges & Solutions

- **Challenge:** Calculating and formatting uptime correctly.
  - **Solution:** Store a global `START_TIME` when the app starts and compute the time difference on each request, returning both seconds and a human-readable `"{hours} hours, {minutes} minutes"` string.

- **Challenge:** Making the app configurable without changing code.
  - **Solution:** Read `HOST`, `PORT`, and `DEBUG` from environment variables with sensible defaults, so the same code can run in different environments.

### 6. GitHub Community

- **Why starring repositories matters:**  
  Starring repositories is a lightweight way to bookmark useful projects and signal appreciation to maintainers. A higher star count helps good projects become more visible, attract contributors, and build trust in the open-source community.

- **How following developers helps:**  
  Following professors, TAs, and classmates makes it easier to discover new projects, see how others solve problems, and stay connected with your learning community. Over time this builds a professional network and exposes you to real-world development practices.

