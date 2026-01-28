# Lab 01 — DevOps Info Service (FastAPI)  
  
## 1. Framework Selection  
  
### Chosen Framework: FastAPI  
  
### Decision Rationale  
  
FastAPI was selected as the web framework for this DevOps Info Service due to its modern design, high performance, and strong suitability for API-centric applications.  
  
Key reasons for choosing FastAPI:  
  
1. **API-First Design**  
   - FastAPI is designed specifically for building REST APIs  
   - Automatic JSON serialization and request handling  
   - Clear separation between routing logic and business logic  
  
2. **High Performance**
   - Asynchronous request handling using `async/await`  
   - Excellent performance for concurrent requests  
  
3. **Modern Python Features**  
   - Native support for type hints  
   - Asynchronous endpoints improve scalability  
   - Clean and explicit API structure  
  
4. **Production Readiness**  
   - Widely adopted in modern backend systems
   - Excellent documentation
  
---  
  
### Framework Comparison  
  
| Feature | Flask | FastAPI         | Django |  
|------|------|-----------------|--------|  
| **Complexity** | Low | Medium          | High |
| **Performance** | Good | Best (async)    | Good |  
| **Async Support** | Limited | Native          | Limited |  
| **Auto API Docs** | No | Yes   | No |  
| **Best For** | Simple apps | Modern APIs     | Full-stack apps |  
| **Our Use Case** | Good | **Best choice** | Overkill |  
  
---  
  
### Why FastAPI Over Flask or Django?  
  
**Flask**  
- Requires additional extensions for async features  
- No built-in API documentation  
- Better suited for very small prototypes  
  
**Django**  
- Too heavyweight for a simple service  
- Includes unneeded features such as admin panel, ORM, templating  
- Designed for monolithic web applications  
  
**Conclusion**  
  
FastAPI provides the best balance between simplicity, performance, and modern best practices. It fits perfectly with the DevOps course focus on microservices, containerization, and cloud-native applications.  
  
---  
  
## 2. Best Practices Applied  
  
### 2.1. Configuration via Environment Variables

```python
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```
**Why it matters:**  
  
- Supports multiple environments (development, production)  
    - Required for Docker and Kubernetes  
    - Follows 12-Factor App methodology  
      

---   
### 2.2. Logging  
  
**Practice: Structured Logging**  

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```
  
**Why it matters:**  
  
- Essential for debugging and observability  
- Significantly helpful for troubleshooting
- Supports different log levels (INFO, ERROR, DEBUG) which allows filtering
      
---  
  
### 2.3 Error Handling  
  
**Practice: Custom Exception Handlers**  
  

```python
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "Endpoint does not exist"
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )
```
**Why it matters:**  
  
- Consistent JSON error responses  
    - Avoids default HTML error pages  
    - Improves client-side error handling  
      
---  

  
### 2.4 Timezone Handling  
  
**Practice: UTC Everywhere**  
  
`datetime.now(timezone.utc).isoformat()`  
  
**Why it matters:**  
  
- Prevents timezone-related bugs  
    - Standard approach for distributed systems  
    - Simplifies log correlation and monitoring  
      
---  
  
### 2.6 Dependency Management  
  
**Practice: Pinned Versions in `requirements.txt`**  
   
 ```python
fastapi==0.115.0
uvicorn[standard]==0.32.0
``` 
**Why it matters:**  
  
- Reproducible builds  
    - Predictable deployments  
    - Safe CI/CD pipelines  
      
---  
  
## 3. API Documentation  
  
### Endpoint: GET /  
  
**Description:**  Returns service metadata, system information, runtime data, request details, and available endpoints.  
  
**Test Command (Request):**  
  
`curl http://localhost:5000/`  
  
**Response Example:**  
  
`{   "service": {     "name": "devops-info-service",     "version": "1.0.0",     "description": "DevOps course info service",     "framework": "FastAPI"   },   "system": {     "hostname": "Honor_MagicBook",     "platform": "Windows",     "platform_version": "Windows NT 10.0",     "architecture": "AMD64",     "cpu_count": 16,     "python_version": "3.13.1"   },   "runtime": {     "uptime_seconds": 120,     "uptime_human": "0 hours, 2 minutes",     "current_time": "2026-01-28T09:45:00+00:00",     "timezone": "UTC"   },   "request": {     "client_ip": "127.0.0.1",     "user_agent": "curl/8.16.0",     "method": "GET",     "path": "/"   },   "endpoints": [     { "path": "/", "method": "GET", "description": "Service information" },     { "path": "/health", "method": "GET", "description": "Health check" }   ] }`  
  

---  
  
### Endpoint: GET /health  
  
**Description:**  Health check endpoint used for monitoring systems.  
  
**Test Command:**  
  
`curl http://localhost:5000/health`  
  
**Response Example:**  
  
`{   "status": "healthy",   "timestamp": "2026-01-28T09:46:00+00:00",   "uptime_seconds": 130 }`  
  
**Use Cases:**  
  
- Kubernetes liveness and readiness probes  
    - Load balancer health checks  
    - Monitoring and alerting systems  
      
---  
  
## 4. Testing Evidence  
  
Screenshots located in `app_python/docs/screenshots/`:  
  
1. `01-root-endpoint.png` — GET /  
2. `02-health-endpoint.png` — GET /health  
3. `03-formatted-json.png` — formatted JSON output  
   

### Terminal Output Example:
```
(venv) PS D:\PycharmProjects\DevOps-Core-Course\app_python> python app.py
INFO:     Started server process [37556]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
2026-01-28 20:24:14,722 - app - INFO - Main endpoint accessed
INFO:     127.0.0.1:55558 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:55561 - "GET /health HTTP/1.1" 200 OK
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [37556]
(venv) PS D:\PycharmProjects\DevOps-Core-Course\app_python> 
```

---  
  
## 5. Challenges & Solutions  
  
### Challenge 1: Human-Readable Uptime  
  
**Problem:**  Raw uptime in seconds is not convenient for humans and monitoring 
  
**Solution:**  Implemented a helper function returning both seconds and a readable format.  


```python
def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes"
    }
```
---  
  
### Challenge 2: Consistent Error Responses  
  
**Problem:**  Default framework errors may return verbose responses.  
  
**Solution:**  Custom exception handlers ensure consistent JSON responses.  

---  
  
### Challenge 3: Cross-Platform System Information  
  
**Problem:**  System information differs between operating systems.  
  
**Solution:**  Used Python standard libraries (`platform`, `socket`) to ensure portability across Windows, macOS, and Linux.  

---  
  
## GitHub Community

Starring repositories is important in open source because it helps highlight valuable projects, supports maintainers, and makes it easier for others to discover reliable and actively used tools.

Following developers on GitHub helps in team projects and professional growth by keeping track of their work, learning from their practices, and building professional connections within the developer community.
