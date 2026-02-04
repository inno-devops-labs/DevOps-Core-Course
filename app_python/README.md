# DevOps Info Service

## Overview

Python Flask service with endpoints for checking system information and health.

## Prerequisites

Python version 3.12 or higher, Flask 3.1.0.

Project has been tested with python 3.12 and Flask 3.1.0 on Ubuntu 24.04

## Installation

```bash
# clone repo
git clone https://github.com/iu-capstone-ad/DevOps-Core-Course
# cd into the app directory
cd app_python
# create and activate a new venv
python3 -m venv venv
source venv/bin/activate
# install dependencies from requirements.txt
pip install -r requirements.txt
```

## Running the Application

```bash
python app.py
# or with custom config
PORT=8080 python app.py
```

## API Endpoints

- `GET /` - Show system information.
- `GET /health` - Show health information (service uptime).

## Configuration

Environment Variables table

| Variable | Default   | Description                          |
|----------|-----------|--------------------------------------|
| `HOST`   | `0.0.0.0` | Address for the service to listen on |
| `PORT`   | `5000`    | Port for the service to listen on    |
| `DEBUG`  | `False`   | Enable Flask debug mode              |

## Docker

### Building the image locally

```bash
cd app_python
docker build -t iucapstonead/devops-info-service:lab02 .
```

### Running the container

```bash
docker run -p 5000:5000 iucapstonead/devops-info-service:lab02
```

### Pulling and running from docker hub

```bash
docker pull iucapstonead/devops-info-service:lab02
```
