# DevOps Info Service

## Overview

DevOps Info Service is a simple web application built with **FastAPI**.  
It provides information about the running service, system environment, and application health status.  
The project is created as part of a DevOps course and serves as a foundation for future labs (CI/CD, containers, monitoring).

---

## Prerequisites

Before running the application, make sure you have:

- Python **3.11** or newer
- `pip` package manager
- (Recommended) Virtual environment support

Check your Python version:

```bash
python --version
```

---

## Installation

1. Navigate to the project directory:

```bash
cd app_python
```

2. Create a virtual environment:

python -m venv venv

3. Activate the virtual environment:

### Windows (PowerShell):

```powershell
venv\Scripts\Activate.ps1
```

### Windows (Command Prompt):

```cmd
venv\Scripts\activate.bat
```

### Linux / macOS:

```bash
source venv/bin/activate
```

4. Install project dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Application

Run the FastAPI application using **uvicorn**:

```bash
uvicorn app:app --host 0.0.0.0 --port 5000
```

The service will be available at:

- http://127.0.0.1:5000/

- http://127.0.0.1:5000/health

Interactive API documentation (Swagger UI):

- http://127.0.0.1:5000/docs

---

## API Endpoints
### GET /

Returns detailed information about the service, system, runtime, and incoming request.

### GET /health

Health check endpoint used for monitoring and readiness probes.

---

## Configuration

The application can be configured using environment variables.

| Variable | Description         | Default |
|----------|---------------------|---------|
| HOST     | Server host address | 0.0.0.0 |
| PORT     | Server port         | 5000    |
| DEBUG    | Enable debug mode   | False   |

### Examples

Run the application with a custom port:

```bash
PORT=8080 uvicorn app:app --host 0.0.0.0 --port 8080
```

Bind the server to localhost only:

```bash
HOST=127.0.0.1 uvicorn app:app --host 127.0.0.1 --port 5000
```

---

## Project Structure

```markdown
app_python/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── tests/
│   └── __init__.py
└── docs/
    ├── LAB01.md
    └── screenshots/
```

---

## Notes

- The application is built using FastAPI.

- Dependencies are pinned in requirements.txt to ensure reproducible builds.

- Logging and error handling are implemented according to best practices.

- The project follows PEP 8 coding standards.