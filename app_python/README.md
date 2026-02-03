# Lab02 - Docker

## Overview
- Daniil Mayorov 
- d.mayorov@innopolis.university
- CBS-01
- 2026 year

**DevOps Info Service** — is a web application that provides detailed information about a service and the system on which it runs.  

**Features:**
- The main endpoint `/` returns information about the service, the system, and the current request
- Endpoint `/health` returns the health status of the service
- Easy configuration via environment variables
- Logging and error handling

---

## Prerequisites

- Python==3.12.0
- Flask==3.1.2
- pip


---

## Installation

1. Clone repository from GitHub:
```bash
git clone https://github.com/Daniil20xx/DevOps-Core-Course.git
```

2. Go to the folder with the code:
```bash
cd app_python
```

3. Prepare the environment

Linux
```bash
python -m venv venv
source venv/bin/activates
```

Windows
```bash
python -m venv venv
.\venv\Scripts\activate 
```

4. Install dependences:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Run application:
```bash
python app.py
```

## API Endpoints

`GET /` - Service and system information

`GET /health` - Health check

## Configuration
| Environment Variable | Default   | Description                 |
| -------------------- | --------- | --------------------------- |
| `HOST`               | `0.0.0.0` | Host to run the application |
| `PORT`               | `8080`    | Port to run the application |
| `DEBUG`              | `False`   | Debug mode (True/False) |


## Docker

This application can be run inside a Docker container.

### Build Docker image locally

To build the Docker image locally, use the Docker build command from the `app_python` directory, specifying the Dockerfile and an image name with a tag.

**Command pattern:**
```bash
docker build -t lab02-python .
```

---

### Run Docker container

After building the image, run the container and map the application port to the host machine so the service is accessible.

**Command pattern:**

```bash
docker run -p <host-port>:<container-port> lab02-python
```

Once the container is running, the application will be available via the mapped port on the host.

---

### Pull image from Docker Hub

The Docker image is also available on Docker Hub and can be pulled directly without building it locally.

**Command pattern:**

Pull:
```bash
docker pull daniil20xx/lab02-python:1.0.0
```

Run:
```bash
docker run -p <host-port>:<container-port> daniil20xx/lab02-python:1.0.0
```


