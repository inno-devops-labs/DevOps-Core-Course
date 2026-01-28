# LAB01 — DevOps Info Service

## 1. Framework Selection

### Chosen Framework: FastAPI

For this laboratory work, **FastAPI** was selected as the web framework for implementing the DevOps Info Service.

### Reasons for Choosing FastAPI

FastAPI was chosen for the following reasons:

- It is a modern and high-performance Python web framework.
- It provides built-in support for asynchronous request handling.
- It automatically generates interactive API documentation (Swagger UI).
- It is widely used in modern production-grade microservices.
- It encourages clean code structure and type hints.

These features make FastAPI a good choice for DevOps-oriented services that may later be containerized, monitored, and scaled.

### Framework Comparison

| Framework | Pros | Cons |
|---------|------|------|
| Flask | Simple, lightweight, easy to learn | Limited built-in features, manual documentation |
| **FastAPI** | High performance, async support, auto docs | Slightly higher learning curve |
| Django | Full-featured, ORM included | Heavyweight, unnecessary complexity for small services |

---

## 2. Best Practices Applied

The following best practices were applied during development:

### 2.1 Virtual Environment

A Python virtual environment (`venv`) is used to isolate project dependencies and avoid conflicts with system-wide packages.

```bash
python -m venv venv
```

**Importance:**  
Ensures reproducible and clean development environments.

---

### 2.2 Dependency Pinning

All dependencies are pinned in `requirements.txt` with exact versions.

```
fastapi==0.115.0  
uvicorn==0.32.0
```

**Importance:**  
Guarantees consistent behavior across different environments.

---

### 2.3 Clean Project Structure

The project follows a clear and logical directory structure separating application code, documentation, tests, and configuration files.

**Importance:**  
Improves readability, maintainability, and scalability of the project.

---

### 2.4 Logging

Structured logging is implemented using Python’s built-in `logging` module.

```
import logging

logging.basicConfig(level=logging.INFO)
```

**Importance:**  
Logging is essential for debugging, monitoring, and production diagnostics.

---

### 2.5 Error Handling

Custom error handlers are implemented for common HTTP errors (404 and 500).

**Importance:**  
Improves user experience and provides predictable API responses.

---

### 2.6 Environment-Based Configuration

Application configuration is controlled via environment variables.

```
PORT = int(os.getenv("PORT", 5000))
```

**Importance:**  
This approach is required for containerized and cloud-native applications.

---

## 3. API Documentation

### 3.1 Available Endpoints

- `GET /` — Returns service, system, runtime, and request information
- `GET /health` — Returns application health status

---

### 3.2 Testing Commands

Test the main endpoint:

```
curl http://127.0.0.1:5000/
```

Test the health check endpoint:

```
curl http://127.0.0.1:5000/health
```

---

### 3.3 Example Response (GET /health)

```
{"status":"healthy","timestamp":"2026-01-28T18:01:28.157878+00:00","uptime_seconds":4983}
```

---

## 4. Testing Evidence

The following screenshots demonstrate the correct operation of the application:

1. **Main Endpoint (`GET /`)**  
   Shows a complete JSON response with service, system, runtime, and request information.

2. **Health Check (`GET /health`)**  
   Confirms the application is running and reports uptime.

3. **Formatted Output**  
   Demonstrates Swagger UI.

All screenshots are located in the `docs/screenshots/` directory.

---

## 5. Challenges & Solutions

### Challenge 1: No Prior Experience with FastAPI  
**Solution:**  
The official FastAPI documentation was studied, and small experiments were conducted to understand routing and request handling.

---

### Challenge 2: PowerShell Execution Policy on Windows  
**Solution:**  
The issue was resolved by adjusting the PowerShell execution policy for the current user, allowing virtual environment activation.

---

### Challenge 3: Git Identity Configuration  
**Solution:**  
Git user name and email were configured globally to enable commit creation and synchronization with GitHub.

---

## 6. GitHub Community

As part of this lab, GitHub social features were explored:

- The course repository `inno-devops-labs/DevOps-Core-Course` was starred.
- The `simple-container-com/api` repository was starred.
- The professor and teaching assistants were followed.
- Classmates `https://github.com/BlazZ1t`, `https://github.com/ph1larmon1a`, `https://github.com/peplxx` were followed.

**Why starring repositories matters:**  
Starring repositories helps bookmark useful projects, supports maintainers, and improves project visibility within the open-source community.

**Why following developers matters:**  
Following developers makes it easier to learn from their work, stay updated on projects, and build professional connections for future collaboration.