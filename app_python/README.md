[![CI/CD](https://github.com/Boogyy/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/Boogyy/DevOps-Core-Course/actions)
[![Ansible Deployment](https://github.com/Boogyy/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/Boogyy/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)


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
| `/visits` | GET    | Returns persisted visits counter                          |

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




---



## Docker Usage

The application is fully containerized and can be built, run, or pulled using Docker.

This approach ensures a consistent runtime environment and simplifies deployment.

---

## Build Image Locally

To build the Docker image locally, use the Dockerfile provided in the `app_python/` directory.

Command pattern:

```bash
docker build -t <image-name>:<tag> .
```

This command:

* Uses a slim Python base image
* Installs dependencies in cached layers
* Runs the application as a non-root user

---

### Run Container

To run the application inside a container and expose it to the host machine, use the following pattern:

```bash
docker run -p <host-port>:<container-port> <image-name>:<tag>
```

Once running, the service will be available via:

* Main endpoint: `http://localhost:<host-port>/`
* Health check: `http://localhost:<host-port>/health`

---

### Pull from Docker Hub


#### Image Tagging Strategy

Tag format used:
```bash
<dockerhub-username>/<image-name>:<tag>
```


Applied tag:
```bash
egorlazutkin/devops-info-service:lab2
```
#### Successful push:
```bash
docker push egorlazutkin/devops-info-service:lab2
...
04cf8f664aa7: Pushed
...
a6866fe8c3d2: Pushed
lab2: digest: sha256:...755ec
```

#### Pulling from Docker Hub
The prebuilt image is available on Docker Hub and can be pulled directly without building locally.

Command pattern:

```bash
docker pull <dockerhub-username>/<image-name>:<tag>
```

```bash
docker pull egorlazutkin/devops-info-service:lab2
...
lab2: Pulling from egorlazutkin/devops-info-service
Digest: sha256:...755ec
Status: Image is up to date for egorlazutkin/devops-info-service:lab2
```



After pulling the image, it can be run using the same `docker run` pattern described above.

---

### Notes

* The container listens on port **5000** by default
* Environment variables can be passed at runtime using `-e`
* The image is designed to be minimal, secure, and production-ready


---

## Badge

The Status Badge is a small dynamic image that shows the current status of the CI/CD pipeline (integrated link to GitHub Actions). Check it on the top

## Testing

This project uses `pytest` for unit testing.

### Run tests locally

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```bash
   cd app_python
   pytest
   ```


## Visits Counter Persistence

The application stores a visits counter in `/data/visits`.

### Local Docker test

```bash
mkdir -p ../monitoring/data
chmod 777 ../monitoring/data

docker compose -f ../monitoring/docker-compose.yml up --build -d app-python

curl http://localhost:5001/
curl http://localhost:5001/
curl http://localhost:5001/visits
cat ../monitoring/data/visits

docker compose -f ../monitoring/docker-compose.yml restart app-python
curl http://localhost:5001/visits
```
