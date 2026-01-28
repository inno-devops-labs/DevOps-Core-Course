## Overview
DevOps Info Service - a web application providing detailed information about itself and its runtime environment.

## Prerequisites
Python == 3.13.9
fastapi == 0.104.1
uvicorn[standard] == 0.24.0
psutil == 5.9.5

## Installation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

## Running the Application
python app.py
# Or with custom config
PORT=8080 python app.py

## API Endpoints
GET / - Service and system information
GET /health - Health check