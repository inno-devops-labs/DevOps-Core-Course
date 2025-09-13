# Python Web Application

## Features

- Displays the current time in Moscow.

## Requirements

- Python 3.10 or later
- Flask
- pytz
- pytest
- black

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:

   ```bash
   python3 -m gunicorn --bind 0.0.0.0:8080 app:app
   ```

2. Open your browser and navigate to:

   ```curl
   http://127.0.0.1:8080
   ```

## Testing (Unit Tests)

Run pytest:

```bash
PYTHONPATH=$(pwd) pytest
```

## Formatting

To format the code, run:

```bash
black .
```

## Docker

### How to Build docker container

```bash
docker build --tag your_docker_username/app_python:v1.0 .
```

### How to Pull image and Run

```bash
docker pull adeepresession/app_python:v1.0
docker run -p 8080:8080 adeepresession/app_python:v1.0
```

## How CI works

### Stages

1. run `black` linter on a project
2. install dependencies
3. run tests with `pytest`
4. run `snyk` vulnerabilities check
5. build docker container
6. login to dockerhub
7. push container to dockerhub
