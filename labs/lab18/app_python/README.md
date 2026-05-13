# User-facing documentation

## Overview 

When acessed, this web service answers with information either about itself (path "/") or with its health status ("/health). The information includes fields with the details of the service, system, runtime, request and enpoints. 

## Prerequisites

### Python version

Pyenv is used for the virtual environment managing. To install it refer to [this website](https://akrabat.com/creating-virtual-environments-with-pyenv/) for instructions.

Python version used: 3.12.9


### Python libraries:
- jsonify imported from Flask library
- request imported from Flask library
- platform
- socket
- datetime imported from datetime
- os
- logging

### Installation

```bash
pyenv virtualenv 3.12.9 webapp
pyenv activate webapp
pip install -r requirements.txt
   ```
### Running the Application
```bash
python app.py
PORT=8080 python app.py # if you want to use a custom port (the default is 5000)
```

### API Endpoints ###
- `GET /` - Service and system information
- `GET /health` - Health check
- `GET /visits` - See the number of times root directory was accessed
- `GET /ready` - Check if the application is ready to take requests
- `GET /health` - Check if the application is dead and should be reloaded

### Configuration ###

| №  | Var name | Description 
| ---| ----- | --------------------|
| #1 | HOST | Name of the host (defaults to socket.hostname first if available) | 
| #2 | PORT | Port for the application access | 
| #3 | DEBUG | Debug status | 

### Docker container ###

#### Building the image locally ###

Use the command in format:
```bash
docker build -t your-docker-username/image-name:image-tag directory-with-dockerfile
```
Example: 
```bash
docker build -t fountainer/my-app:1.1.0 .
```
#### Running a container ###

Use the command in format:
```bash 
docker run -p host-port:container-port image-name:tag
```
Example:
```bash
docker run -p 12345:12345 fountainer/my-app:1.1.0
```
#### Pulling from Docker Hub ###

```bash
docker image pull image-name:image-tag
```

Example: 
```bash
docker image pull app:1.0.0
```

### Testing ###

#### Workflow Badge

[![My FLask App Testing](https://github.com/ffountainer/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=master)](https://github.com/ffountainer/DevOps-Core-Course/actions/workflows/python-ci.yml)

#### Unit testing ####

To test the ./ endpoint:

```bash
pytest ./app_python/tests/test_home_endpoint.py
```

To test the ./health endpoint:


```bash
pytest ./app_python/tests/test_health_endpoint.py
```

## Ansible deployment

[![Ansible Deployment](https://github.com/ffountainer/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/ffountainer/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)