# DevOps Info Service (Lab 01)

## Overview
Simple web service that returns service, system, runtime and request information.

## Prerequisites
- Python 3.11+
- pip
## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
## Running the Application

```bash
python app.py
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
```

## API Endpoints

- `GET /` - Service and system information
- `GET /health` - Health check
## Configuration

|Variable|Default|Description|
|---|---|---|
|HOST|0.0.0.0|Bind host|
|PORT|5000|Bind port|
|DEBUG|False|Flask debug mode