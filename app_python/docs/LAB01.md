# LAB01 – DevOps Info Service

## 1. Framework Selection

### Chosen Framework: **FastAPI**

FastAPI was selected as the backend framework for this laboratory work due to its modern design, high performance, and strong alignment with DevOps and microservice principles.

**Reasons for choosing FastAPI:**

* High performance based on Starlette and Pydantic
* Automatic OpenAPI (Swagger) documentation
* Native async/await support
* Built-in request validation and error handling
* Production-ready and widely adopted

### Comparison with Alternatives

| Framework  | Language   | Performance | Async Support | Docs Generation     | Complexity |
| ---------- | ---------- | ----------- | ------------- | ------------------- | ---------- |
| FastAPI    | Python     | ⭐⭐⭐⭐⭐       | Yes           | Automatic (Swagger) | Low        |
| Flask      | Python     | ⭐⭐⭐         | Limited       | Manual              | Very Low   |
| Django     | Python     | ⭐⭐⭐         | Partial       | Manual              | High       |

**Conclusion:** FastAPI provides the best balance between simplicity, performance, and modern API features for this task.

---

## 2. Best Practices Applied

### 2.1 Structured Logging

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Importance:** Enables observability, debugging, and log aggregation in production environments.

---

### 2.2 Environment-based Configuration

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Importance:** Allows configuration without code changes and follows 12-factor app principles.

---

### 2.3 Health Check Endpoint

```python
@app.get("/health")
def health():
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }
```

**Importance:** Essential for monitoring, orchestration tools (Docker/Kubernetes), and CI/CD pipelines.

---

### 2.4 Centralized Error Handling

```python
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={
        'error': 'Internal Server Error'
    })
```

**Importance:** Prevents application crashes and provides consistent API error responses.

---

## 3. API Documentation

### 3.1 Main Endpoint

**GET /**

**Response Example:**

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "localhost",
    "platform": "Linux",
    "cpu_count": 8
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "0 hours, 2 minutes"
  }
}
```

---

### 3.2 Health Check Endpoint

**GET /health**

**Response Example:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T12:00:00Z",
  "uptime_seconds": 120
}
```

---

### 3.3 Testing Commands

```bash
python app.py
curl http://localhost:5000/
curl http://localhost:5000/health
```

---

## 4. Testing Evidence

* Main endpoint showing complete JSON

![alt text](screenshots/01-main-endpoint.png)
* Health check response

![alt text](screenshots/02-health-check.png)
* Formatted/pretty-printed output

![alt text](screenshots/03-formatted-output.png)

---

## 5. Challenges & Solutions

### Challenge 1: Timezone-safe uptime calculation

**Problem:** Using naive `datetime.now()` caused timezone inconsistencies.

**Solution:** Switched to UTC-aware timestamps using `datetime.now(timezone.utc)`.![alt text](image.png)

### Challenge 2: Global error handling

**Problem:** Unhandled exceptions caused unclear error responses.

**Solution:** Implemented centralized exception handlers using FastAPI decorators.

---

### Challenge 3: Observability

**Problem:** Lack of visibility during request handling.

**Solution:** Added structured logging for endpoints and errors.

---

6. GitHub Community

Starring repositories in open source helps acknowledge maintainers' work, increases project visibility, and encourages continued development by signaling community interest. It also helps developers bookmark useful projects for future reference.

Following developers on GitHub makes it easier to track their work, learn from their coding practices, and stay updated on technologies relevant to team projects and professional growth.

---