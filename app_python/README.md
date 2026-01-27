## Overview
This API contains two endpoints:
1. Getting information about the system
2. Getting the health status of the API itself

## Prerequisites 
```
python==3.13.5
uvicorn==0.40.0
pydantic==2.12.5
fastapi==0.128.0
```

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
python app.py
# Or with custom config
PORT=8080 python app.py
```

## API Endpoints

```
GET / - Service and system information
GET /health - Health check
```

## Configuration

| Variable | Description                            | Type    | Default   | Example     |
| -------- | -------------------------------------- | ------- | --------- |-------------|
| `HOST`   | Host address the application binds to  | string  | `0.0.0.0` | `127.0.0.1` |
| `PORT`   | Port number the application listens on | integer | `5000`    | `8000`      |
| `DEBUG`  | Enables debug mode                     | boolean | `False`   | `True`      |

