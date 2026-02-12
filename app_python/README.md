# Flask App: Moscow Time and Visits Counter

This application displays the current time in Moscow and tracks the number of visits to the root endpoint. The visit count is persisted to a file and exposed via a dedicated endpoint.

## Features

- Displays the current time in Moscow using pytz
- Increments a persistent visit counter on /
- Returns current visit count on /visits
- Unit tests
- HTML and CSS for basic presentation

## Run via Docker image from Docker Hub

```sh
docker pull petrel312/flask_app:latest
docker run -p 5000:5000 petrel312/flask_app:latest
```

## Local Installation and Run

```sh
git clone https://github.com/Petrel321/S25-core-course-labs.git
cd S25-core-course-labs
python3 -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activate
pip install -r requirements.txt
cd app_python
python web.py
```

## Build the Docker Image Locally

```sh
git clone https://github.com/Petrel321/S25-core-course-labs.git
cd S25-core-course-labs/app_python
docker build -t any_docker_image_name .
```

## Run with Docker Compose and Persistence

```sh
cd app_python
mkdir -p data
docker compose up --build
```

The visits counter is stored at /data/visits. The Docker Compose configuration mounts ./data from the host to /data inside the container so the counter is persisted between restarts.

## Endpoints

- / returns the application HTML page and increments the visits counter
- /visits returns the current counter value as JSON

## Unit Test

There is a unit test that checks the application returns a successful response.