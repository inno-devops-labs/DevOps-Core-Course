## Overview
This Python application provides a RESTful service that delivers system and service information through health check endpoints.

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the application with default settings:
```bash
python app.py
```

Or specify a custom port:
```bash
PORT=8080 python app.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service and system information |
| GET | `/health` | Health check status |

## Configuration

Configure the application using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Server port |
| `HOST` | `127.0.0.1` | Server host address |

## Docker Usage

This application can be run inside a Docker container.

### Build the image locally
Use the Dockerfile to build the image from the project source.

Pattern:
```bash
docker build -t <image-name> -f app_python/Dockerfile app_python
```

### Run the container
Run the container interactively to start the application.

Pattern:
```bash
docker run -p <port:port> -it <image-name>
```

### Pull from Docker Hub
The image is publicly available on Docker Hub.

Pattern:
```bash
docker pull <dockerhub-username>/<image-name>:latest
docker run -it <dockerhub-username>/<image-name>:latest
```