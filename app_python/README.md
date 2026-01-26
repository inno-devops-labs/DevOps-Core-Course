# DevOps Info Service

A web application providing detailed system information and health status for DevOps monitoring.

## Overview

This service provides comprehensive information about:
- Service metadata (name, version, description)
- System information (hostname, platform, CPU, etc.)
- Runtime information (uptime, current time)
- Request details (client IP, user agent)
- Health status for monitoring

## Prerequisites

- Python 3.11 or higher
- pip package manager

## Installation

1. Clone the repository
2. Create and activate Python virtual environment:
```
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```
3. Install requirements:
```
pip install -r requirements.txt
```

## Running the Application
```
python app.py
```

With custom configuration:
```
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true python app.py
```

## API Endpoints
- GET / - Service and system information
- GET /health - Health check


## Configuration
| Variable | Default   | Description                     |
| -------- | --------- | ------------------------------- |
| `HOST`   | `0.0.0.0` | Host to bind the server to      |
| `PORT`   | `5000`    | Port to listen on               |
| `DEBUG`  | `False`   | Enable debug mode               |
