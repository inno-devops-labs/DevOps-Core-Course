# Python Web Server

## Overview

This web server provides information about itself and its environment.

## Prerequisites

- Python 3.14.0

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

You can create `.env` file storing all enviroment values. To run application simply type:

```bash
python app.py
```

## API Endpoints

- `GET /` - service data 
- `GET /health` - Health check

## Configuration

Supported enviroment values:

- `HOST` - address of the application
- `PORT` - port of the application
- `DEBUG` - `[true/false]` do/don't enable debug features