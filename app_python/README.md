# Overview
Lightweight web application built using __FastAPI__. It provides essential service and system information, along with a health check endpoint to monitor application status. The application shares various details about the server environment, including runtime status and configuration.

## Prerequisites

Before you begin, ensure you have the following prerequisites:

Python Version: Python 3.11 or higher
Dependencies: The application depends on the FastAPI framework and other packages specified in the requirements.txt file.

## Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application
```bash python app.py
# Or with custom config
PORT=8080 python app.py
```


## API Endpoints

| Method | Endpoint   | Description                             |
|--------|------------|-----------------------------------------|
| GET    | /          | Service and system information.         |
| GET    | /health    | Health check for the application.      |

### `/` - Service and System Information
This endpoint returns information about the service, system details, and configuration.

### `/health` - Health Check
This endpoint returns the health status of the application along with the current timestamp.


## Configuration

| Environment Variable | Description                             | Default Value |
|----------------------|-----------------------------------------|---------------|
| `HOST`               | The host address for the application.  | `0.0.0.0`     |
| `PORT`               | The port the application listens on.   | `5000`        |
| `DEBUG`              | Enables debug mode if set to `true`.  | `false`       |