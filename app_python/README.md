# DevOps Info Service — FastAPI Implementation

## Overview

The **DevOps Info Service** is a web application that provides detailed information about itself and the system it runs on.  
It exposes two main endpoints:

- **GET /** — Returns service metadata, system information, runtime statistics, and request details.  
- **GET /health** — Returns service health status and uptime for monitoring purposes.  

This application serves as the foundation for DevOps labs involving containerization, CI/CD, monitoring, and deployments.

---

## Prerequisites

- **Python version:** 3.10+  
- **Dependencies:** Listed in requirements.txt


## Installation

1. Create a virtual environment:


```bash
python -m venv venv
```

2. Activate the virtual environment:

```bash
# macOS/Linux
source venv/bin/activate

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Application

1. Start the application with default settings:

```bash
uvicorn app:app --reload --port 5000
```

2. Start with custom configuration:

```bash
HOST=127.0.0.1 PORT=8080 uvicorn app:app --reload
```

3. Access endpoints:

* Main info: `http://127.0.0.1:5000/`
* Health check: `http://127.0.0.1:5000/health`



## API Endpoints

| Endpoint  | Method | Description                                               |
| --------- | ------ | --------------------------------------------------------- |
| `/`       | GET    | Returns service, system, runtime, and request information |
| `/health` | GET    | Returns service health status and uptime                  |

**Example request:**

```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/health
```

---

## Configuration

The application can be configured via environment variables:

| Variable | Default   | Description                           |
| -------- | --------- | ------------------------------------- |
| `HOST`   | `0.0.0.0` | Host to bind the application          |
| `PORT`   | `5000`    | Port to run the application           |
| `DEBUG`  | `false`   | Enable debug mode (`true` or `false`) |

---

## Logging

* All requests are logged with timestamp, method, and path.
* Errors (404, 500) are logged and returned as JSON.

---

## Error Handling

* **404 Not Found:** Returned if endpoint does not exist.
* **500 Internal Server Error:** Returned if an unexpected error occurs.

```json
{
  "error": "Not Found",
  "message": "Endpoint does not exist"
}
```

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

---

## Notes

* Tested with Python 3.10.7
* Dependencies pinned in `requirements.txt` for reproducibility:

  * `fastapi==0.115.0`
  * `uvicorn[standard]==0.32.0`
