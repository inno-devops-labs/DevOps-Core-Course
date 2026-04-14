![CI](https://github.com/Ray3264/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)

# DevOps Info Service

## Overview
A simple Python web service that provides system, runtime, and request information.
Built as a foundation for DevOps monitoring tools.

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
# run with default configuration (0.0.0.0:8080)
python app.py

# run with custom host and port
HOST=127.0.0.1 PORT=8080 DEBUG=True python app.py
```

* **HOST** - IP address to bind the server (default: `0.0.0.0`)
* **PORT** - Port number to run the application (default: `8080`)
* **DEBUG** - Enables debug mode with auto-reload (default: `False`)

## API Endpoints
   - `GET /` - Service and system information
   - `GET /visits` - Current persisted visits counter
   - `GET /health` - Health check
### Configuration

The application can be configured using environment variables:

| Variable | Default   | Description                                                 |
| -------- | --------- | ----------------------------------------------------------- |
| `HOST`   | `0.0.0.0` | IP address to bind the server                               |
| `PORT`   | `8080`    | Port number to run the application                          |
| `DEBUG`  | `False`   | Enable debug mode (auto-reload and detailed error messages) |
| `VISITS_FILE` | `/data/visits` | File path for persisted visits counter                |

## Checking the Service

After starting the application, open a browser or use curl:
```bash
curl http://localhost:8080/
curl http://localhost:8080/visits
curl http://localhost:8080/health
```

Expected result:

/ returns JSON with service, system, runtime, and request information

/visits returns persisted visits counter

/health returns service health status and uptime

## Running with Docker
 Build Docker Image
```bash
docker build -t devops-info-python .
```
Run Docker Container
```bash
docker run -p 8080:8080 -v "$(pwd)/data:/data" devops-info-python
```

For custom port mapping:
```bash
docker run -p 5000:8080 -v "$(pwd)/data:/data" devops-info-python
```

Then open in browser:

* http://localhost:8080/

* http://localhost:8080/health

### Docker Compose (persistence check)
```bash
docker compose up --build -d
curl http://localhost:8080/
curl http://localhost:8080/visits
docker compose restart
curl http://localhost:8080/visits
```

The counter value is stored in `./data/visits` and survives container restart.

## Project Structure
```
app_python/
├── app.py
├── requirements.txt
├── Dockerfile
├── README.md
├── docs/
│   ├── LAB01.md
│   └── LAB02.md
└── .dockerignore
```
## Notes

* This service uses Flask development server and is intended for educational purposes only

* Not recommended for production without a proper WSGI server (e.g. Gunicorn)

* Environment variables can be overridden both locally and in Docker