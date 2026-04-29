# Lab 1 — DevOps Info Service: Web Application Development

![difficulty](https://img.shields.io/badge/difficulty-beginner-success)
![topic](https://img.shields.io/badge/topic-Web%20Development-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![languages](https://img.shields.io/badge/languages-Python%20|%20Go-informational)

> Build a DevOps info service that reports system information and health status. This service will evolve throughout the course into a comprehensive monitoring tool.

## Overview

Create a **DevOps Info Service** - a web application providing detailed information about itself and its runtime environment. This foundation will grow throughout the course as you add containerization, CI/CD, monitoring, and persistence.

**What You'll Learn:**
- Web framework selection and implementation
- System introspection and API design
- Python best practices and documentation
- Foundation for future DevOps tooling

**Tech Stack:** Python 3.11+ | Flask 3.1 or FastAPI 0.115

---

## Tasks

### Task 1 — Python Web Application (6 pts)

Build a production-ready Python web service with comprehensive system information.

#### 1.1 Project Structure

Create this structure:

```
app_python/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── .gitignore               # Git ignore
├── README.md                # App documentation
├── tests/                   # Unit tests (Lab 3)
│   └── __init__.py
└── docs/                    # Lab documentation
    ├── LAB01.md            # Your lab submission
    └── screenshots/        # Proof of work
        ├── 01-main-endpoint.png
        ├── 02-health-check.png
        └── 03-formatted-output.png
```

#### 1.2 Choose Web Framework

Select and justify your choice:
- **Flask** - Lightweight, easy to learn
- **FastAPI** - Modern, async, auto-documentation
- **Django** - Full-featured, includes ORM

Document your decision in `app_python/docs/LAB01.md`.

#### 1.3 Implement Main Endpoint: `GET /`

Return comprehensive service and system information:

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
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-07T14:30:00.000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

<details>
<summary>💡 Implementation Hints</summary>

**Get System Information:**
```python
import platform
import socket
from datetime import datetime

hostname = socket.gethostname()
platform_name = platform.system()
architecture = platform.machine()
python_version = platform.python_version()
```

**Calculate Uptime:**
```python
start_time = datetime.now()

def get_uptime():
    delta = datetime.now() - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }
```

**Request Information:**
```python
# Flask
request.remote_addr  # Client IP
request.headers.get('User-Agent')  # User agent
request.method  # HTTP method
request.path  # Request path

# FastAPI
request.client.host
request.headers.get('user-agent')
request.method
request.url.path
```

</details>

#### 1.4 Implement Health Check: `GET /health`

Simple health endpoint for monitoring:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

Return HTTP 200 for healthy status. This will be used for Kubernetes probes in Lab 9.

<details>
<summary>💡 Implementation Hints</summary>

```python
# Flask
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    })

# FastAPI
@app.get("/health")
def health():
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }
```

</details>

#### 1.5 Configuration

Make your app configurable via environment variables:

```python
import os

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Test:**
```bash
python app.py                    # Default: 0.0.0.0:5000
PORT=8080 python app.py          # Custom port
HOST=127.0.0.1 PORT=3000 python app.py
```

---

### Task 2 — Documentation & Best Practices (4 pts)

#### 2.1 Application README (`app_python/README.md`)

Create user-facing documentation:

**Required Sections:**
1. **Overview** - What the service does
2. **Prerequisites** - Python version, dependencies
3. **Installation**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Running the Application**
   ```bash
   python app.py
   # Or with custom config
   PORT=8080 python app.py
   ```
5. **API Endpoints**
   - `GET /` - Service and system information
   - `GET /health` - Health check
6. **Configuration** - Environment variables table

#### 2.2 Best Practices

Implement these in your code:

**1. Clean Code Organization**
- Clear function names
- Proper imports grouping
- Comments only where needed
- Follow PEP 8

<details>
<summary>💡 Example Structure</summary>

```python
"""
DevOps Info Service
Main application module
"""
import os
import socket
import platform
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))

# Application start time
START_TIME = datetime.now(timezone.utc)

def get_system_info():
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'architecture': platform.machine(),
        'python_version': platform.python_version()
    }

@app.route('/')
def index():
    """Main endpoint - service and system information."""
    # Implementation
```

</details>

**2. Error Handling**

<details>
<summary>💡 Implementation</summary>

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500
```

</details>

**3. Logging**

<details>
<summary>💡 Implementation</summary>

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info('Application starting...')
logger.debug(f'Request: {request.method} {request.path}')
```

</details>

**4. Dependencies (`requirements.txt`)**

```txt
# Web Framework
Flask==3.1.0
# or
fastapi==0.115.0
uvicorn[standard]==0.32.0  # Includes performance extras
```

Pin exact versions for reproducibility.

**5. Git Ignore (`.gitignore`)**

```gitignore
# Python
__pycache__/
*.py[cod]
venv/
*.log

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

#### 2.3 Lab Submission (`app_python/docs/LAB01.md`)

Document your implementation:

**Required Sections:**
1. **Framework Selection**
   - Your choice and why
   - Comparison table with alternatives
2. **Best Practices Applied**
   - List practices with code examples
   - Explain importance of each
3. **API Documentation**
   - Request/response examples
   - Testing commands
4. **Testing Evidence**
   - Screenshots showing endpoints work
   - Terminal output
5. **Challenges & Solutions**
   - Problems encountered
   - How you solved them

**Required Screenshots:**
- Main endpoint showing complete JSON
- Health check response
- Formatted/pretty-printed output

#### 2.4 GitHub Community Engagement

**Objective:** Explore GitHub's social features that support collaboration and discovery.

**Actions Required:**
1. **Star** the course repository
2. **Star** the [simple-container-com/api](https://github.com/simple-container-com/api) project — a promising open-source tool for container management
3. **Follow** your professor and TAs on GitHub:
   - Professor: [@Cre-eD](https://github.com/Cre-eD)
   - TA: [@marat-biriushev](https://github.com/marat-biriushev)
   - TA: [@pierrepicaud](https://github.com/pierrepicaud)
4. **Follow** at least 3 classmates from the course

**Document in LAB01.md:**

Add a "GitHub Community" section (after Challenges & Solutions) with 1-2 sentences explaining:
- Why starring repositories matters in open source
- How following developers helps in team projects and professional growth

<details>
<summary>💡 GitHub Social Features</summary>

**Why Stars Matter:**

**Discovery & Bookmarking:**
- Stars help you bookmark interesting projects for later reference
- Star count indicates project popularity and community trust
- Starred repos appear in your GitHub profile, showing your interests

**Open Source Signal:**
- Stars encourage maintainers (shows appreciation)
- High star count attracts more contributors
- Helps projects gain visibility in GitHub search and recommendations

**Professional Context:**
- Shows you follow best practices and quality projects
- Indicates awareness of industry tools and trends

**Why Following Matters:**

**Networking:**
- See what other developers are working on
- Discover new projects through their activity
- Build professional connections beyond the classroom

**Learning:**
- Learn from others' code and commits
- See how experienced developers solve problems
- Get inspiration for your own projects

**Collaboration:**
- Stay updated on classmates' work
- Easier to find team members for future projects
- Build a supportive learning community

**Career Growth:**
- Follow thought leaders in your technology stack
- See trending projects in real-time
- Build visibility in the developer community

**GitHub Best Practices:**
- Star repos you find useful (not spam)
- Follow developers whose work interests you
- Engage meaningfully with the community
- Your GitHub activity shows employers your interests and involvement

</details>

---

## Bonus Task — Compiled Language (2.5 pts)

Implement the same service in a compiled language to prepare for multi-stage Docker builds (Lab 2).

**Choose One:**
- **Go** (Recommended) - Small binaries, fast compilation
- **Rust** - Memory safety, modern features
- **Java/Spring Boot** - Enterprise standard
- **C#/ASP.NET Core** - Cross-platform .NET

**Structure:**

```
app_go/  (or app_rust, app_java, etc.)
├── main.go
├── go.mod
├── README.md
└── docs/
    ├── LAB01.md              # Implementation details
    ├── GO.md                 # Language justification
    └── screenshots/
```

**Requirements:**
- Same two endpoints: `/` and `/health`
- Same JSON structure
- Document build process
- Compare binary size to Python

<details>
<summary>💡 Go Example Skeleton</summary>

```go
package main

import (
    "encoding/json"
    "net/http"
    "os"
    "runtime"
    "time"
)

type ServiceInfo struct {
    Service  Service  `json:"service"`
    System   System   `json:"system"`
    Runtime  Runtime  `json:"runtime"`
    Request  Request  `json:"request"`
}

var startTime = time.Now()

func mainHandler(w http.ResponseWriter, r *http.Request) {
    info := ServiceInfo{
        Service: Service{
            Name:    "devops-info-service",
            Version: "1.0.0",
        },
        System: System{
            Platform:     runtime.GOOS,
            Architecture: runtime.GOARCH,
            CPUCount:     runtime.NumCPU(),
        },
        // ... implement rest
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(info)
}

func main() {
    http.HandleFunc("/", mainHandler)
    http.HandleFunc("/health", healthHandler)

    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }

    http.ListenAndServe(":"+port, nil)
}
```

</details>

---

## How to Submit

1. **Create Branch:**
   ```bash
   git checkout -b lab01
   ```

2. **Commit Work:**
   ```bash
   git add app_python/
   git commit -m "feat: implement lab01 devops info service"
   git push -u origin lab01
   ```

3. **Create Pull Requests:**
   - **PR #1:** `your-fork:lab01` → `course-repo:master`
   - **PR #2:** `your-fork:lab01` → `your-fork:master`

4. **Verify:**
   - All files present
   - Screenshots included
   - Documentation complete

---

## Acceptance Criteria

### Main Tasks (10 points)

**Application Functionality (3 pts):**
- [ ] Service runs without errors
- [ ] `GET /` returns all required fields:
  - [ ] Service metadata (name, version, description, framework)
  - [ ] System info (hostname, platform, architecture, CPU, Python version)
  - [ ] Runtime info (uptime, current time, timezone)
  - [ ] Request info (client IP, user agent, method, path)
  - [ ] Endpoints list
- [ ] `GET /health` returns status and uptime
- [ ] Configurable via environment variables (PORT, HOST)

**Code Quality (2 pts):**
- [ ] Clean code structure
- [ ] PEP 8 compliant
- [ ] Error handling implemented
- [ ] Logging configured

**Documentation (3 pts):**
- [ ] `app_python/README.md` complete with all sections
- [ ] `app_python/docs/LAB01.md` includes:
  - [ ] Framework justification
  - [ ] Best practices documentation
  - [ ] API examples
  - [ ] Testing evidence
  - [ ] Challenges solved
  - [ ] GitHub Community section (why stars/follows matter)
- [ ] All 3 required screenshots present
- [ ] Course repository starred
- [ ] simple-container-com/api repository starred
- [ ] Professor and TAs followed on GitHub
- [ ] At least 3 classmates followed on GitHub

**Configuration (2 pts):**
- [ ] `requirements.txt` with pinned versions
- [ ] `.gitignore` properly configured
- [ ] Environment variables working

### Bonus Task (2.5 points)

- [ ] Compiled language app implements both endpoints
- [ ] Same JSON structure as Python version
- [ ] `app_<language>/README.md` with build/run instructions
- [ ] `app_<language>/docs/GO.md` with language justification
- [ ] `app_<language>/docs/LAB01.md` with implementation details
- [ ] Screenshots showing compilation and execution

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Functionality** | 3 pts | Both endpoints work with complete, correct data |
| **Code Quality** | 2 pts | Clean, organized, follows Python standards |
| **Documentation** | 3 pts | Complete README and lab submission docs |
| **Configuration** | 2 pts | Dependencies, environment vars, .gitignore |
| **Bonus** | 2.5 pts | Compiled language implementation |
| **Total** | 12.5 pts | 10 pts required + 2.5 pts bonus |

**Grading Scale:**
- **10/10:** Perfect implementation, excellent documentation
- **8-9/10:** All works, good docs, minor improvements possible
- **6-7/10:** Core functionality present, basic documentation
- **<6/10:** Missing features or documentation, needs revision

---

## Resources

<details>
<summary>📚 Python Web Frameworks</summary>

- [Flask 3.1 Documentation](https://flask.palletsprojects.com/en/latest/)
- [Flask Quickstart](https://flask.palletsprojects.com/en/latest/quickstart/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [Django 5.1 Documentation](https://docs.djangoproject.com/en/5.1/)

</details>

<details>
<summary>🐍 Python Best Practices</summary>

- [PEP 8 Style Guide](https://pep8.org/)
- [Python Logging Tutorial](https://docs.python.org/3/howto/logging.html)
- [Python platform module](https://docs.python.org/3/library/platform.html)
- [Python socket module](https://docs.python.org/3/library/socket.html)

</details>

<details>
<summary>🔧 Compiled Languages (Bonus)</summary>

- [Go Web Development](https://golang.org/doc/articles/wiki/)
- [Go net/http Package](https://pkg.go.dev/net/http)
- [Rust Web Frameworks](https://www.arewewebyet.org/)
- [Spring Boot Quickstart](https://spring.io/quickstart)
- [ASP.NET Core Tutorial](https://docs.microsoft.com/aspnet/core/)

</details>

<details>
<summary>🛠️ Development Tools</summary>

- [Postman](https://www.postman.com/) - API testing
- [HTTPie](https://httpie.io/) - Command-line HTTP client
- [curl](https://curl.se/) - Data transfer tool
- [jq](https://stedolan.github.io/jq/) - JSON processor

</details>

---

## Looking Ahead

This service evolves throughout the course:

- **Lab 2:** Containerize with Docker, multi-stage builds
- **Lab 3:** Add unit tests and CI/CD pipeline
- **Lab 8:** Add `/metrics` endpoint for Prometheus
- **Lab 9:** Deploy to Kubernetes using `/health` probes
- **Lab 12:** Add `/visits` endpoint with file persistence
- **Lab 13:** Multi-environment deployment with GitOps

---

**Good luck!** 🚀

> **Remember:** Keep it simple, write clean code, and document thoroughly. This foundation will carry through all 16 labs!