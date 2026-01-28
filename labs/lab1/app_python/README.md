# DevOps Info Service (Python / Flask)

A small web service that exposes basic system and runtime information via HTTP.
This project is part of **DevOps Core Course — Lab 1**.

## Overview
The service provides:
- `GET /` — JSON with service metadata, system info, runtime info, request info, and available endpoints
- `GET /health` — JSON health check with uptime

## Prerequisites
- Python 3.12+ (tested on Python 3.12.8)
- `pip` / `venv`

## Installation
```bash
cd app_python

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
## Running the Application

Default config:

`python app.py`

Custom config (environment variables):

`HOST=127.0.0.1 PORT=8080 python app.py`

## API Endpoints

### `GET /`

Returns JSON containing:

- service metadata (name, version, description, framework)
    
- system info (hostname, platform, architecture, CPU count, python version)
    
- runtime info (uptime, current time, timezone)
    
- request info (client IP, user agent, method, path)
    
- endpoints list
    

Example:

`curl http://localhost:5000/`

### `GET /health`

Returns service health and uptime.

Example:

`curl http://localhost:5000/health`

## Configuration

|Variable|Default|Description|
|---|---|---|
|`HOST`|`0.0.0.0`|Bind address|
|`PORT`|`5000`|Listening port|
|`DEBUG`|`false`|Flask debug mode|

## Screenshots

See: `app_python/docs/screenshots/`

- `index.png` — main endpoint output
    
- `health.png` — health endpoint output
    
- `terminal_start_custom_port.png` — app started with custom HOST/PORT
    
- `web_custom_port.png` — main endpoint opened on custom port
    

## Notes

- `venv/` is intentionally ignored via `.gitignore` and must not be committed.