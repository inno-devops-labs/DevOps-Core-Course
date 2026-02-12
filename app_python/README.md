## DevOps Info Service (Python)

[![Python CI](https://github.com/abdughafforzoda/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/abdughafforzoda/DevOps-Core-Course/actions/workflows/python-ci.yml)

### Overview

This is a simple **DevOps Info Service** implemented in Python using **Flask**.  
It exposes HTTP endpoints that return detailed information about the service, the underlying system, and its runtime environment.  
The service will be used as a foundation for future labs (containerization, CI/CD, monitoring, and more).

### Prerequisites

- **Python**: 3.11 or newer
- **Pip**: Python package manager
- Recommended: virtual environment (`venv`)

### Installation

```bash
cd app_python

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Running the Application

Default configuration (host `0.0.0.0`, port `5000`):

```bash
python app.py
```

Custom configuration using environment variables:

```bash
PORT=8080 python app.py

HOST=127.0.0.1 PORT=3000 DEBUG=true python app.py
```

### API Endpoints

- `GET /`
  - Returns service metadata, system information, runtime information, request details, and a list of available endpoints.
- `GET /health`
  - Simple health check returning service status and uptime.

### Configuration

The application can be configured using the following environment variables:

| Variable | Default   | Description                          |
|---------|-----------|--------------------------------------|
| `HOST`  | `0.0.0.0` | Address to bind the HTTP server to   |
| `PORT`  | `5000`    | Port to listen on                    |
| `DEBUG` | `False`   | Enable Flask debug mode if `true`    |

Examples:

```bash
HOST=127.0.0.1 PORT=8000 python app.py
DEBUG=true python app.py
```

### Docker

The application can be run as a Docker container.

**Build the image locally:**

```bash
docker build -t devops-info-service .
```

**Run a container:**

```bash
docker run -p 5000:5000 devops-info-service
```

Map the container port (5000) to a host port of your choice: `-p <host_port>:5000`.  
Override `PORT` or `HOST` with environment variables if needed.

**Pull from Docker Hub:**

```bash
docker pull jambulancia/devops-info-service
docker run -p 5000:5000 jambulancia/devops-info-service
```

### Testing

```bash
cd app_python
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pytest tests/ -v
```
