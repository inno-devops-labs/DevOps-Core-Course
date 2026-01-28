# devops-info-service (Python)

## Overview

This is the Python implementation of the DevOps Info Service.  
It provides endpoints to get detailed information about the service, system, runtime, and health status.

## Prerequisites

- Python 3.11 or higher
- Dependencies listed in `requirements.txt`

## Installation

```bash
python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Unix or Git Bash
source venv/bin/activate

pip install -r requirements.txt
```

## Run

```
# Run with default host and port (0.0.0.0:5000)
python app.py

# Or specify host and port via environment variables
# Windows PowerShell
$env:HOST=127.0.0.1
$env:PORT=8080
python app.py

# Unix / Bash
HOST=127.0.0.1 PORT=8080 python app.py
```

## API Endpoints

- `GET /` - Service and system information
- `GET /health` - Health check

## Troubleshooting

If the server does not start or you get errors about execution policy on Windows PowerShell, try:

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

If the port is busy, find and kill the process:

```
netstat -ano | findstr :5000
taskkill /PID <pid> /F
```

## Licence

MIT Licence
`To be made`
