# devops-info-service (Python)

[![Python CI + Docker Build](https://github.com/SfedBro/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab03)](https://github.com/SfedBro/DevOps-Core-Course/actions/workflows/python-ci.yml)

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

## Docker

This application is containerized using Docker for easy deployment and consistency across environments.

### Build Docker Image Locally

```
docker build -t sfedbro/app_python:lab02 .
```

### Run Container Locally

```
docker run -p 5000:5000 sfedbro/app_python:lab02
```

Access the app at http://localhost:5000 .

### Pull and Run from Docker Hub

```
docker pull sfedbro/app_python:lab02
docker run -p 5000:5000 sfedbro/app_python:lab02
```

## Testing

This project uses pytest for unit testing.

To run tests locally:

```bash
pytest -v
```

## Licence

MIT Licence

```

```
