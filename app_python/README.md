# DevOps Course Info Service

## Overview

DevOps Info Service - small Flask based service what return and report system metadata and information.

## Prerequisites
- Python 3.11+
- pip 
-  Linux / macOS / Windows

## Installation guid

1. Clone the repository:
   ```bash
   git clone git@github.com:setterwars/DevOps-Core-Course.git
   
2. Navigate to the project directory:
   ```bash
   cd app_python

3. (Optional) Create and activate a virtual environment:
   ```bash
    python3 -m venv venv

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt

5. Run the application:
    ```bash
    python3 app.py # in default mode
    PORT=8080 HOST=127.0.0.1 DEBUG=True python3 app.py # in custom mode

## Available Endpoints
- `GET /` - Returns system metadata including hostname, IP address, and current timestamp.
- `GET /health` - Returns the health status of the service.