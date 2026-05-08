### Overview

The DevOps Info Service is a Python-based web application that provides detailed information about the service itself, the underlying system, runtime environment, and incoming requests. It serves as a foundation for future labs, where containerization, CI/CD, monitoring, and persistence will be added. This service is ideal for learning web development, system introspection, and best practices in Python.

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git (for cloning the repository)
- Optional: curl or HTTP client for testing endpoints

### Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the application
```bash
# run with default configuration (0.0.0.0:5000)
python app.py

# run with custom host and port
HOST=127.0.0.1 PORT=8080 DEBUG=True python app.py
```

* **HOST** - IP address to bind the server (default: `0.0.0.0`)
* **PORT** - Port number to run the application (default: `5000`)
* **DEBUG** - Enables debug mode with auto-reload (default: `False`)

### API Endpoints
- `GET /` - Service and system information
- `GET /health` - Health check

### Configuration

The application can be configured using environment variables:

| Variable | Default   | Description                                                 |
| -------- | --------- | ----------------------------------------------------------- |
| `HOST`   | `0.0.0.0` | IP address to bind the server                               |
| `PORT`   | `5000`    | Port number to run the application                          |
| `DEBUG`  | `False`   | Enable debug mode (auto-reload and detailed error messages) |

### Docker

The application can be run as a Docker container, which removes the need to install Python and dependencies locally. A prebuilt image is also available on Docker Hub.

#### Building the image locally

To build the Docker image from the provided `Dockerfile`, use a build command pattern similar to:

```bash
docker build -t <image-name>:<tag> .
```

Where:

* `<image-name>` is the name you want to give the image
* `<tag>` is typically a version or `latest`

#### Running the container

Once the image is built (or pulled), you can run the application in a container using a run command pattern like:

```bash
docker run -p <host-port>:<container-port> \
  -e HOST=<host> \
  -e PORT=<port> \
  -e DEBUG=<true|false> \
  <image-name>:<tag>
```

Notes:

* The container exposes port `5000` by default
* Environment variables work the same way as when running the app locally
* Port mapping allows access to the service from your host machine

#### Pulling the image from Docker Hub

A prebuilt image is available on Docker Hub:

[https://hub.docker.com/r/glebpp/app_python](https://hub.docker.com/r/glebpp/app_python)

To pull the image, use a pull command pattern such as:

```bash
docker pull <dockerhub-username>/<repository>:<tag>
```

After pulling the image, you can run it using the same container run pattern described above.
