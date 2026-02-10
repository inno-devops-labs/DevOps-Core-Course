# DevOps Info Service (Flask)

## Overview
A simple DevOps information service that displays system, runtime, and request data.  
Includes a health-check endpoint for monitoring.

## Prerequisites
- Python 3.12+
- Flask 3.1.2

## Installation
```bash
python -m venv venv

#Linux
source venv/bin/activate       
#Windows: 
venv\Scripts\activate

pip install -r requirements.txt
```

## Running the Application
```bash
python app.py
```

Custom configuration via environment variables:
```bash
#In bash or linux
HOST=127.0.0.1 PORT=8080 python app.py

#In Windows PowerShell
$env:HOST=127.0.0.1
$env:PORT="8080"
python app.py
```


## API Endpoints
| Method | Path | Description |
|---------|------|--------------|
| GET | `/` | Returns system and service information |
| GET | `/health` | Returns health and uptime status |

## Configuration
| Variable | Default | Description |
|-----------|----------|-------------|
| HOST | 0.0.0.0 | Host address |
| PORT | 5000 | Listening port |
| DEBUG | False | Enables Flask debug mode |

## Docker

The application can be run in a container. The image runs as a non-root user and listens on port 5000.

### Build the image locally
From the `app_python/` directory, run `docker build` with a tag (e.g. `devops-info-service:latest`).
```
docker build -t <image-name>:<tag> .
```

### Run a container
Use `docker run` with port mapping so the app is reachable on the host (e.g. map container port 5000 to a host port 5000):
```
docker run -d -p <host-port>:5000 --name <container-name> <image-name>:<tag>
```
After `docker run` you can view long via this command:
```
docker logs <container-name>
```

### Pull from Docker Hub
You can pull latest app from docker hub:
```
docker pull chaleshka/devops-info-service:latest
```
And run as:
```
docker run -d -p <host-port>:5000 --name <container-name> chaleshka/devops-info-service:latest
```

## Testing
Install dependencies (pytest), then run:
```
python -m pytest
```
After run and all passed tests you must see something like this:

=================================== test session starts ====================================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0
rootdir: G:\DevOps\DevOps-Core-Course\app_python
plugins: anyio-4.9.0, langsmith-0.3.15
collected 4 items                                                                           

tests\test_app.py <span style="color:green">.... [100%]</span>

<span style="color:green">==================================== 4 passed in 0.44s =====================================</span>

