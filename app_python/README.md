# DevOps Info Service (Python)

## Overview
A small web service that reports service metadata, system info, runtime uptime, and request details.  
It provides two endpoints: `/` (full info) and `/health` (health check).

## Prerequisites
- Python **3.11+**
- pip

## Installation
```bash
cd app_python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application
   ```bash
   python app.py
   ```
## API Endpoints
   - `GET /` - Service and system information
   - `GET /health` - Health check

## Configuration 
    ```bash
    HOST = "0.0.0.0"
    PORT = "5000"
    DEBUG = "False"
    ```