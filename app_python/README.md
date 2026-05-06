# Moscow Time App

## Overview

This is a simple Python web application built with Flask.  
It displays the current time in Moscow and updates it every time the page is refreshed.

## Requirements

- Python 3.11+
- Flask 3.1.3+
- gunicorn 25.3.0+

## Installation

1. Create a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Launch application via Gunicorn:

    ```bash
    gunicorn -b {IP}:{PORT} app:app
    ```

## Usage

```bash
gunicorn -b 127.0.0.1:8080 app:app
```


## Docker

Build the Docker image:

```bash
docker build -t moscow-time-app:1.0.0 .
```

Run the container in the background:

```bash
docker run --rm -d --name moscow-time-app -p 8080:8080 moscow-time-app:1.0.0
```

Check that the application works:

```bash
curl http://localhost:8080
```

Check that the container is not running as root:

```bash
docker exec moscow-time-app id
```

Stop the container:

```bash
docker stop moscow-time-app
```

### Docker Hub

Log in to Docker Hub:

```bash
docker login
```

Tag the image:

```bash
docker tag moscow-time-app:1.0.0 <dockerhub_username>/moscow-time-app:1.0.0
```


Push the image:

```bash
docker push <dockerhub_username>/moscow-time-app:1.0.0
```


Pull the image:

```bash
docker pull <dockerhub_username>/moscow-time-app:1.0.0
```


Run the pulled image:

```bash
docker run --rm -d --name moscow-time-app -p 8080:8080 <dockerhub_username>/moscow-time-app:1.0.0
```


Check the pulled image:

```bash
curl http://localhost:8080
```
