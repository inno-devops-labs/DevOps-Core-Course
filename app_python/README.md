[![CI Pipeline](https://github.com/KaramKhaddour/S25-core-course-labs/actions/workflows/CI.yml/badge.svg)](https://github.com/KaramKhaddour/S25-core-course-labs/actions/workflows/CI.yml)

# Moscow Time Display Application (FastAPI)

## Overview

This application is built using FastAPI and provides the current time in Moscow. It is lightweight and fast.

## Prerequisites

Ensure you have Python installed on your system. This application requires Python 3.7 or later.

## Installation

1. Clone the repository :

   ```sh
   git clone https://github.com/KaramKhaddour/S25-core-course-labs.git
   cd S25-CORE-CORSE-LABS/app_python
   ```

2. Install the required dependencies:

   ```sh
   pip install -r requirements.txt
   ```

## Running the Application

To start the FastAPI server, run the following command:

```sh
uvicorn main:app --reload
```

This will start the development server and enable automatic reloading for changes in the source code.

## Accessing the API

Once the application is running, you can access it via:

- **API Endpoint:** `http://127.0.0.1:8000` (or another specified host/port)
- **Interactive API Documentation:**
  - Swagger UI: `http://127.0.0.1:8000/docs`

## Docker Instructions

This application can be built and run as a Docker container.

### Build the Docker Image

To build the Docker image, run:

```bash
docker build -t my-fastapi-app .
```

### Run the Docker Container

To run the container:

```bash
docker run -d -p 8000:8000 my-fastapi-app
```

### Pull the Docker Image

If you have pushed your Docker image to Docker Hub, pull it using:

```bash
docker pull karamkhaddourpro/my-fastapi-app
```

### Running the Pulled Image

```bash
docker run -d -p 8000:8000 karamkhaddourpro/my-fastapi-app
```

### Running tests

```bash
pytest 
```

## Lab 12 Additions – Visit Counter & Persistence

These additions were implemented as part of Lab 12:

1. **Persistent Visit Counter**
   - Each visit to the main page (`/`) increments a counter stored in `./data/visits.txt`.
   - The counter persists across container restarts because of the Docker volume.

2. **New Endpoint `/visits`**
   - Returns the total number of visits as plain text.
   - Example:

     ```bash
     curl http://127.0.0.1:8000/visits
     # Output: 5
     ```

3. **Updated `/` Endpoint**
   - Now increments the visit counter automatically on each page load.
   - Optionally, the visit count can be displayed on the main page (requires updating `index.html`).

4. **Docker Compose Volume**
   - Ensures `visits.txt` persists on the host machine:  

     ```yaml
     volumes:
       - ./data:/data
     ```


## Docker Compose

The `docker-compose.yml` provides persistent storage for the visit counter:

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data  # Mount host data folder for persistent visit count
```
Run the app with:
```
docker compose up --build
```

This ensures that visits.txt persists across container restarts.

