# DevOps Info Service (FastAPI)

[![Python CI (app_python)](https://github.com/fayz131/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/fayzullin/DevOps-Core-Course/actions/workflows/python-ci.yml)


## Overview
DevOps Info Service is a web application that provides information about the running service and the system it is running on. The application is designed as a foundation for future DevOps labs, including containerization, CI/CD, and monitoring.

## Prerequisites
- Python 3.11 or newer
- pip
- Python virtual environment (venv)

## Installation
Navigate to the application directory:

cd app_python

Create and activate a virtual environment:

python3 -m venv venv
source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

## Running the Application
Start the application:

python app.py

Run with custom configuration:

HOST=127.0.0.1 PORT=8080 python app.py

## API Endpoints

GET /
Returns service, system, runtime, and request information.

GET /health
Returns application health status and uptime.

## Configuration

Environment variables:

HOST — server host (default: 0.0.0.0)  
PORT — server port (default: 5000)

## Docker

### Build image

```bash
docker build -t devops-info-service:lab2 .
```

Run container  
```bash
docker run --rm -p 5000:5000 devops-info-service:lab2
```

From Docker Hub  
```bash
docker pull fayzullin/devops-info-service:lab2
docker run --rm -p 5000:5000 fayzullin/devops-info-service:lab2
```

## Testing

Install dev dependencies and run tests:

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
```


