[![Python CI/CD Pipeline](https://github.com/MisABU148/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/MisABU148/DevOps-Core-Course/actions/workflows/python-ci.yml)

# DevOps Info Service

## Overview
A Python web service that provides comprehensive system information and monitoring endpoints for DevOps purposes. The service returns detailed information about the host system, runtime statistics, and request metadata.

## Prerequisites
- Python 3.12 or higher
- pip package manager

## Installation

1. Clone the repository:
```bash
git clone https://github.com/MisABU148/DevOps-Core-Course.git
cd app_python
```

2. Create and activate virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Docker installation

1. Clone the repository:
```bash
git clone https://github.com/MisABU148/DevOps-Core-Course.git
cd DevOps-Core-Course/app_python
```

2. Build Docker image:
```bash
docker build -t devops-info-service:latest
```

3. Or pull from Docker Hub:
```bash
docker pull mariablood/devops-info-service:latest
```

## Running the Application

1. Local
```bash
python app.py
```
2. Docker
```bash
docker run -d -p 5000:5000 --name devops-app devops-info-service:latest
# or docker hub
docker run -d -p 5000:5000 --name devops-app mariablood/devops-info-service:latest
```

## Testing
This project uses **pytest** as the testing framework for unit and integration testing.
```bash
pytest -v
```
