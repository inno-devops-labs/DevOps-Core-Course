# **LAB01 — DevOps Info Service**

## **1. Framework Selection**

For this project, I selected **FastAPI** as the web framework.

### **Why FastAPI**
FastAPI is a modern, high‑performance Python framework designed for building APIs quickly and cleanly. It fits the DevOps workflow extremely well because:

- **High performance** — one of the fastest Python frameworks.
- **Asynchronous support** — handles many requests efficiently.
- **Automatic API documentation** — Swagger UI and ReDoc included by default.
- **Clean and minimal code** — reduces boilerplate.
- **Great for microservices** — easy to containerize and deploy.

### **Comparison with Alternatives**

| Feature | Flask | FastAPI | Django |
|--------|--------|---------|--------|
| Performance | Medium | **High** | Medium |
| Async support | No | **Yes** | Partial |
| Auto‑documentation | No | **Yes** | No |
| Learning curve | Easy | **Easy** | Hard |
| Microservice‑friendly | Yes | **Yes** | Not ideal |
| Built‑in ORM | No | No | **Yes** |

**Conclusion:** FastAPI is the best choice for a lightweight, modern DevOps information service.

---

## **2. Best Practices Applied**

### **2.1 Clean Code Organization**
- Functions are separated logically (`get_uptime()`, `get_system_info()`).
- Imports are grouped and structured.
- Code follows PEP 8 style guidelines.
- Comments are used only where necessary.

### **2.2 Logging**
The application uses Python’s `logging` module:

- INFO logs for normal operations.
- DEBUG logs when `DEBUG=true` is enabled.
- Error logs for unexpected issues.

Example:

```python
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
```

### **2.3 Error Handling**
Custom handlers were added:

```python
@app.exception_handler(404)
@app.exception_handler(500)
```

These return JSON responses instead of default HTML error pages.

### **2.4 Environment‑Based Configuration**
The service supports:

| Variable | Default | Description |
|----------|----------|-------------|
| `HOST` | 0.0.0.0 | Server bind address |
| `PORT` | 5000 | Port number |
| `DEBUG` | false | Enables debug mode |
| `LOG_LEVEL` | INFO | Logging verbosity |

### **2.5 Dependency Management**
All dependencies are pinned in `requirements.txt` for reproducibility.

---

## **3. API Documentation**

### **3.1 GET /**  
Returns full service, system, runtime, and request information.

Example request:

```bash
curl http://localhost:5000/
```

Example response (shortened):

```json
{
  "service": { ... },
  "system": { ... },
  "runtime": { ... },
  "request": { ... },
  "endpoints": [ ... ]
}
```

---

### **3.2 GET /health**

Health‑check endpoint used for monitoring and Kubernetes probes.

Example:

```bash
curl http://localhost:5000/health
```

Response:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T20:00:00Z",
  "uptime_seconds": 42
}
```

---

## **4. Testing Evidence**

Screenshots included in `docs/screenshots/`:

- **01-main-endpoint.png** — output of `/`
- **02-health-check.png** — output of `/health`
- **03-formatted-output.png** — pretty‑printed JSON (e.g., via `jq`)

Example pretty‑print command:

```bash
curl http://localhost:5000/ | jq
```

---

## **5. Challenges & Solutions**

### **Challenge 1: Environment variables on Windows**
Windows does not support Linux‑style:

```
DEBUG=true python app.py
```

**Solution:** use PowerShell syntax:

```powershell
$env:DEBUG="true"
python app.py
```

---

### **Challenge 2: No logging in the initial version**
Added structured logging with configurable log levels.

---

### **Challenge 3: FastAPI did not start with `python app.py`**
Added:

```python
if __name__ == "__main__":
    uvicorn.run(...)
```

Now both methods work:
- `python app.py`
- `uvicorn app:app`

---

## **6. GitHub Community**

### **Why starring repositories matters**
- Stars help highlight useful open‑source projects.
- They increase project visibility and credibility.
- They show appreciation to maintainers.
- They reflect your technical interests on your GitHub profile.

### **Why following developers matters**
- You discover new tools through their activity.
- You learn from their code, commits, and projects.
- It builds a professional network — essential for DevOps careers.
- Following classmates helps with collaboration and team projects.
