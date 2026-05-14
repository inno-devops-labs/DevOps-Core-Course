# Overview
This app have been build for the lab01 of the "Devops Core course". It give service and
system information and do health check for monitoring

# Prerequisites
```markdown
python 3.14.4
```
# Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

# Running the Application
```bash
python app.py
# Or with custom config
PORT=4999 HOST 127.0.0.1 python app.py
 ```
# API Endpoints
 - ==GET /== - Service and system information
 - ==GET /health== - Health check

# Configuration

|HOST|PORT|
-----|-----
|Host ip| tcp port number|
