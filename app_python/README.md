# DevOps Info Service
A lightweight demo Python web application that system information via HTTP endpoints

### Prerequisites
Python 3.10+
Flask 3.1.0

### Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Application
```bash
python3 app.py
# Or with custom config
PORT=8080 python3 app.py
```

### API Endpoints
There are few main endpoints:
- `GET /` - Service and system information
- `GET /health` - Health check.

### Configuration

| Variable | Value  | Purpose                              |
| -------- | ------ | ------------------------------------ |
| Host     | string | A host to run app on                 |
| Port     | int    | A port to assign for web application |
| Debug    | bool   | Should debug output be enabled       |

## Docker
This application can be run in a containerized environment with Docker

### Build the image locally
To build the Docker image, use the Docker build command from the project directory, specifying the Dockerfile and an image name with a tag
```bash
cd app_python
docker build -t <image-name> .
```

### Run a container
To run the application, start a container from the built image and map the container port to a port on the host machine so the application can be accessed locally
```bash
docker run -p<any-port-on-your-machine>:5000 <created-image-name>
```

### Pull from Docker Hub
The pre-built image is also available on Docker Hub and can be pulled using the standard Docker pull command with the repository name and desired tag
```bash
docker pull cacucoh/testiks:1.0
```