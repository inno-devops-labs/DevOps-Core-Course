## Overview
This API contains three endpoints:
1. Getting information about the system (increments visit counter on each call)
2. Getting the health status of the API itself
3. Getting the total visit count for the root endpoint

## Prerequisites 
```
python==3.13.5
uvicorn==0.40.0
pydantic==2.12.5
fastapi==0.128.0
```

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
python app.py
# Or with custom config
PORT=8080 python app.py
```

## API Endpoints

```
GET /        - Service and system information (increments visit counter)
GET /health  - Health check
GET /visits  - Total visit count for the root endpoint
```

## Configuration

| Variable      | Description                              | Type    | Default         | Example            |
| ------------- | ---------------------------------------- | ------- | --------------- | ------------------ |
| `HOST`        | Host address the application binds to    | string  | `0.0.0.0`       | `127.0.0.1`        |
| `PORT`        | Port number the application listens on   | integer | `5000`          | `8000`             |
| `DEBUG`       | Enables debug mode                       | boolean | `False`         | `True`             |
| `VISITS_FILE` | Path to the file storing the visit count | string  | `/data/visits`  | `/tmp/visits`      |

## Visits Counter

The application tracks how many times the root endpoint `/` has been accessed.  
The counter is stored in a plain text file (default: `/data/visits`) and survives container restarts as long as the file is on a persistent volume.

### Local testing with Docker Compose

```bash
# Start the container
docker-compose up -d

# Access the root endpoint a few times
curl http://localhost:5000/
curl http://localhost:5000/
curl http://localhost:5000/

# Check the counter via the API
curl http://localhost:5000/visits
# → {"visits": 3}

# Check the raw file on the host
cat ./data/visits
# → 3

# Restart the container — the counter continues from the last value
docker-compose restart
curl http://localhost:5000/visits
# → {"visits": 3}
```

## Docker

1. Building the image
    example:
    ```bash
    docker build -t <image_name>:<tag> <context>
    ```
    
    to build our service used:
    ```bash
    docker duild -t devops-info-service:latest .
    ```
2. Running a container
    example:
    ```bash
    docker run <options> <image_name>
    ```
    
    to run our service used:
    ```bash
    docker run -d -p 5000:5000 devops-info-service
    ```
   
3. Pulling from Docker Hub example:
    ```bash
    docker pull <repo_name> 
    ```
    
    to pull our repo used:
    ```bash
    docker pull th1ef/devops-info-service:latest
    ```
