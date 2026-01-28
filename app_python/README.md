# DevOps Info Service

> A web service that provides comprehensive system and runtime information for DevOps monitoring and diagnostics.

## Overview

This is a Flask-based web application that exposes system information, runtime metrics, and health check endpoints. Built as part of the DevOps Core Course Lab 1, this service will evolve throughout the course to include containerization, CI/CD, monitoring, and persistence features.

## Prerequisites

- **Python 3.11+** (tested with Python 3.11)
- **pip** package manager
- **Virtual environment** (recommended)

## Installation

### 1. Clone the repository

```bash
cd app_python
```

### 2. Create a virtual environment

**Option A: Using python3 (recommended)**
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate   # On Windows
```

**Option B: Using python (if python3 not found)**
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate   # On Windows
```

**Option C: Using python module (always works)**
```bash
python3 -m venv venv  # or just 'python -m venv venv'
source venv/bin/activate
```

### 3. Install dependencies

**Option A: Using pip3 (recommended)**
```bash
pip3 install -r requirements.txt
```

**Option B: Using pip (if pip3 not found)**
```bash
pip install -r requirements.txt
```

**Option C: Using python module (always works)**
```bash
python3 -m pip install -r requirements.txt
# or
python -m pip install -r requirements.txt
```

## Running the Application

### Development Mode

**Option A: Using python3 (recommended)**
```bash
python3 app.py
```

**Option B: Using python (if python3 not found)**
```bash
python app.py
```

The server will start on `http://0.0.0.0:3000` by default.

### Custom Configuration

You can configure the application using environment variables:

**With python3:**
```bash
# Run on a different port
PORT=8080 python3 app.py

# Run on localhost only
HOST=127.0.0.1 python3 app.py

# Enable debug mode
DEBUG=true python3 app.py

# Combine multiple settings
HOST=127.0.0.1 PORT=3000 DEBUG=true python3 app.py
```

**With python (if python3 not available):**
```bash
PORT=8080 python app.py
HOST=127.0.0.1 python app.py
DEBUG=true python app.py
HOST=127.0.0.1 PORT=3000 DEBUG=true python app.py
```

### Production Mode (with Gunicorn)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

### `GET /`

Returns comprehensive service and system information.

**Response Example:**

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "MacBook-Pro.local",
    "platform": "Darwin",
    "platform_version": "23.2.0",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.11.5"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-28T12:00:00.000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "Mozilla/5.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service and system information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check endpoint"
    }
  ]
}
```

### `GET /health`

Health check endpoint for monitoring systems and Kubernetes probes.

**Response Example:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T12:00:00.000Z",
  "uptime_seconds": 3600
}
```

**Status:** Always returns `200 OK` if the service is running.

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host address |
| `PORT` | `3000` | Server port number |
| `DEBUG` | `False` | Enable Flask debug mode |

## Testing

### Using curl

```bash
# Test main endpoint
curl http://localhost:3000/

# Test health endpoint
curl http://localhost:3000/health
```

### Pretty-print JSON responses

**Option A: Using jq (if installed)**
```bash
curl http://localhost:3000/ | jq .
curl http://localhost:3000/health | jq .
```

**Option B: Using python3 -m json.tool**
```bash
curl http://localhost:3000/ | python3 -m json.tool
curl http://localhost:3000/health | python3 -m json.tool
```

**Option C: Using python -m json.tool (if python3 not found)**
```bash
curl http://localhost:3000/ | python -m json.tool
curl http://localhost:3000/health | python -m json.tool
```

**Option D: Save to file and inspect**
```bash
curl http://localhost:3000/ > response.json
cat response.json
```

### Using browser

Open in your browser:
- Main endpoint: http://localhost:3000/
- Health check: http://localhost:3000/health

### Using HTTPie (if installed)

```bash
http http://localhost:3000/
http http://localhost:3000/health
```

## Project Structure

```
app_python/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── tests/                # Unit tests (Lab 3)
│   └── __init__.py
└── docs/                 # Documentation
    ├── LAB01.md         # Lab 1 submission report
    └── screenshots/      # Proof of work
```

## Development

### Code Style

This project follows PEP 8 Python style guidelines:
- Use 4 spaces for indentation
- Maximum line length: 79 characters for code
- Descriptive function and variable names
- Docstrings for all public functions

### Adding New Endpoints

To add a new endpoint, define a new route in `app.py`:

```python
@app.route('/your-endpoint')
def your_function():
    return jsonify({'message': 'Your response'}), 200
```

## Troubleshooting

### Python Command Issues

#### Problem: `python3: command not found`

**Solution 1:** Check if you have `python` instead:
```bash
python --version
```

**Solution 2:** Install Python via Homebrew (macOS):
```bash
brew install python@3.14
which python3
python3 --version
```

**Solution 3:** Install Python via apt (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
```

**Solution 4:** Install Python via yum (CentOS/RHEL):
```bash
sudo yum install python3 python3-pip
```

#### Problem: `python: command not found`

**Solution:** Use `python3` instead (this is normal on modern systems):
```bash
python3 app.py
python3 -m venv venv
```

### pip/pip3 Command Issues

#### Problem: `pip3: command not found` or `pip: command not found`

**Solution 1:** Use python module (always works):
```bash
python3 -m pip install -r requirements.txt
# or
python -m pip install -r requirements.txt
```

**Solution 2:** Upgrade pip:
```bash
python3 -m pip install --upgrade pip
```

**Solution 3:** Use ensurepip:
```bash
python3 -m ensurepip --upgrade
```

### Virtual Environment Issues

#### Problem: `venv: command not found`

**Solution 1:** Use the module directly:
```bash
python3 -m venv venv
# or
python -m venv venv
```

**Solution 2:** Install venv module (Ubuntu/Debian):
```bash
sudo apt-get install python3-venv
```

**Solution 3:** Install venv module (CentOS/RHEL):
```bash
sudo yum install python3-venv
```

#### Problem: Virtual environment activation fails

**macOS/Linux:**
```bash
source venv/bin/activate
echo $VIRTUAL_ENV  # Should show path
```

**Windows (cmd):**
```cmd
.\venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

### Port Already in Use

**Problem:** `Address already in use` or `Port 3000 is already in use`

**Solution 1:** Find and kill the process (macOS/Linux):
```bash
lsof -i :3000
kill -9 PID  # replace PID with actual number
```

**Solution 2:** Find process (Linux alternative):
```bash
netstat -tlnp | grep 3000
ss -tlnp | grep 3000
```

**Solution 3:** Find process (Windows):
```cmd
netstat -ano | findstr :3000
```

**Solution 4:** Use different port:
```bash
PORT=8080 python3 app.py
PORT=5000 python app.py
```

### Module/Import Issues

#### Problem: `ModuleNotFoundError: No module named 'flask'`

**Solution 1:** Install in virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
# or
python3 -m pip install -r requirements.txt
```

**Solution 2:** Verify venv is activated:
```bash
which python  # Should show venv/bin/python
echo $VIRTUAL_ENV  # Should show venv path
```

#### Problem: `ModuleNotFoundError: No module named 'json'`

**Solution:**
```bash
python3 -c "import json; print('OK')"
```

### JSON Formatting Issues

#### Problem: `python3 -m json.tool` not working

**Solution 1:** This should always work:
```bash
python3 -m json.tool
```

**Solution 2:** Use jq instead:
```bash
curl http://localhost:3000/ | jq .
```

**Solution 3:** Install jq:
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# CentOS/RHEL
sudo yum install jq
```

### curl Command Issues

#### Problem: `curl: command not found`

**Solution 1:** Install curl (macOS):
```bash
brew install curl
```

**Solution 2:** Install curl (Ubuntu/Debian):
```bash
sudo apt-get install curl
```

**Solution 3:** Install curl (CentOS/RHEL):
```bash
sudo yum install curl
```

**Solution 4:** Use Python instead:
```bash
python3 -c "import requests; print(requests.get('http://localhost:3000/').json())"
```

#### Problem: `Connection refused`

**Solution 1:** Make sure app is running:
```bash
python3 app.py  # In another terminal
```

**Solution 2:** Check if server is listening:
```bash
# macOS/Linux
lsof -i :3000
netstat -an | grep 3000
```

### Windows-specific Issues

#### Problem: `PowerShell execution policy error`

**Solution:** Run as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Problem: `'\venv\Scripts\activate' is not a valid batch file`

**Solution:** Use the right activation script:
```cmd
# For cmd.exe
.\venv\Scripts\activate.bat

# For PowerShell
.\venv\Scripts\Activate.ps1
```
