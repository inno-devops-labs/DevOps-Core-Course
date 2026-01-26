# DevOps Info Service (Flask)

## Overview
A simple DevOps information service that displays system, runtime, and request data.  
Includes a health-check endpoint for monitoring.

## Prerequisites
- Python 3.12+
- Flask 3.1.2

## Installation
```bash
python -m venv venv

#Linux
source venv/bin/activate       
#Windows: 
venv\Scripts\activate

pip install -r requirements.txt
```

## Running the Application
```bash
python app.py
```

Custom configuration via environment variables:
```bash
#In bash or linux
HOST=127.0.0.1 PORT=8080 python app.py

#In Windows PowerShell
$env:HOST=127.0.0.1
$env:PORT="8080"
python app.py
```


## API Endpoints
| Method | Path | Description |
|---------|------|--------------|
| GET | `/` | Returns system and service information |
| GET | `/health` | Returns health and uptime status |

## Configuration
| Variable | Default | Description |
|-----------|----------|-------------|
| HOST | 0.0.0.0 | Host address |
| PORT | 5000 | Listening port |
| DEBUG | False | Enables Flask debug mode |
