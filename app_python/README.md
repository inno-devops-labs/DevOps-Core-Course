# DevOps Info Service

A Python web service that reports system information and health status through a simple REST API.

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
cd app_python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```bash
python app.py
```

With custom configuration:

```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true python app.py
```

For production, use gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

### GET /

Returns service info, system details, runtime stats, and request information.

```bash
curl http://localhost:5000/ | python -m json.tool
```

### GET /health

Health check for monitoring and container orchestration.

```bash
curl http://localhost:5000/health
```

## Configuration

| Variable | Default   | Description  |
| -------- | --------- | ------------ |
| `HOST`   | `0.0.0.0` | Host address |
| `PORT`   | `5000`    | Port number  |
| `DEBUG`  | `false`   | Debug mode   |

## Troubleshooting

**Port in use:** Use a different port with `PORT=8080 python app.py`

**Import errors:** Make sure venv is activated and dependencies are installed

**Permission denied:** Use port > 1024 or run with elevated privileges
