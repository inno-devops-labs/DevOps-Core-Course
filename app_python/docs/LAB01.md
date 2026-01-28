# Lab 1 - DevOps Info Service: Web Application Initialisation

## Overview

This service provides detailed information about itself and its runtime environment. It exposes endpoints to retrieve system info, runtime status, and health check, forming a foundation for further DevOps tooling.
**Prerequisites**
Python 3.11+
Dependencies listed in `requirements.txt` (FastAPI, Uvicorn)

## Installation

```bash
python -m venv venv

# For Windows PowerShell
.\venv\Scripts\Activate.ps1
# For Unix or Git Bash
source venv/bin/activate

pip install -r requirements.txt
```

**Running the Application**

```bash
# Classic launch 0.0.0.0:5000
python app.py

# Or with custom config
# Windows PowerShell:
$env:HOST=127.0.0.1
$env:PORT=8080
python app.py

# Unix / Bash:
HOST=127.0.0.1 PORT=8080 python app.py
```

**Example**

After server launches go to http://localhost:5000, http://localhost:PORT, or http://HOST:PORT
For example above: http://127.0.0.1:8080
For information add `/health` or `/docs` (http://localhost:5000/docs)

**Troubleshooting**

For windows Powershell
If you do not see logs like:

```pgsql
INFO:     Uvicorn running on http://0.0.0.0:5000
```

try activating your virtual environment manually:

```powershell
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error, check current policy:

```powershell
Get-ExecutionPolicy -Scope Process
```

If result is `Restricted`, allow bypass temporarily:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
Y
```

Try running the server again.
If the server still won't start, check if the port is already in use:

```powershell
# replace 5000 with your PORT
netstat -ano | findstr :5000
```

If you see something like:

```nginx
  TCP    0.0.0.0:5000           0.0.0.0:0              LISTENING       1234
```

Stop the occupying process with:

```powershell
taskkill /PID 1234 /F
```

If issues persist, search online with your error details.

**API Endpoints**

- `GET /` - Service and system information
- `GET /health` - Health check

  **Configuration** - Environment variables table
  | Environment Variable | Description | Default |
  | -------------------- | --------------------------- | ------- |
  | HOST | Server host address | 0.0.0.0 |
  | PORT | Server port | 5000 |
  | DEBUG | Debug mode (`true`/`false`) | false |

1.  **Framework Selection**
    - Your choice and why
      FastAPI, since it automates API documentation generation which saves time and improves maintainability. It supports asynchronous code, is fast, and widely adopted in modern Python web development.
    - Comparison table with alternatives
      | Framework | Description | Pros | Cons |
      | --------- | ------------------------- | --------------------------- | ------------------------------- |
      | Flask | Lightweight web framework | Simple, easy to learn | Manual doc setup |
      | FastAPI | Modern async framework | Auto docs, high performance | Slightly steeper learning curve |
      | Django | Full-featured framework | Built-in ORM and admin | Heavy for simple APIs |

2.  **Best Practices Applied**
    - List practices with code examples
    - Explain importance of each

      **Clean Code Organization**
      - Clear function names and logical grouping
      - Minimal and meaningful comments

      **PEP 8 Compliance**
      - Follows Python styling for readability and maintainability

      **Error Handling**
      - Custom handlers for 404 and 500 errors to provide meaningful responses

      **Logging**
      - Logging configured to track server start and request info, aiding debugging

      **Configuration via Environment Variables**
      - Enables flexible deployment without code changes

3.  **API Documentation**
    - Request/response examples
    - Testing commands

      ```bash
        curl -X 'GET' \
        'http://localhost:5000/' \
        -H 'accept: application/json'
      ```

      ```json
      {
         "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI"
         },
         "system": {
            "hostname": "SfedBroPC",
            "platform": "Windows",
            "architecture": "AMD64",
            "cpu_count": 16,
            "python_version": "3.12.7"
         },
         ...(truncated?)
      }
      ```

      **Response headers**
      content-length: 710
      content-type: application/json
      date: Sun,25 Jan 2026 20:19:03 GMT
      server: uvicorn

      **Responses**
      200
      Successful Response

4.  **Testing Evidence**
    - Screenshots showing endpoints work
    - Terminal output

PS C:\Users\Admin\Desktop\DevOps-Core-Course\app_python> Invoke-RestMethod http://localhost:5000/

service : @{name=devops-info-service; version=1.0.0; description=DevOps course info service; framework=FastAPI}
system : @{hostname=SfedBroPC; platform=Windows; architecture=AMD64; cpu_count=16; python_version=3.12.7}
runtime : @{uptime_seconds=142; uptime_human=0 hours, 2 minutes; current_time=2026-01-25T20:16:36.142484+00:00; timezone=UTC}
request : @{client_ip=127.0.0.1; user_agent=Mozilla/5.0 (Windows NT; Windows NT 10.0; ru-RU) WindowsPowerShell/5.1.19041.6456; method=GET; path=/}
endpoints : {@{path=/; method=GET; description=Service information}, @{path=/health; method=GET; description=Health check}}

5.  **Challenges & Solutions**
    - Problems encountered
      Did not know API
      Could not launch the application
      Small documentation experience
    - How you solved them
      Searched the web
      Looked in AI and web for advices
      Spent few hours writing and editing

6.  <details>
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
