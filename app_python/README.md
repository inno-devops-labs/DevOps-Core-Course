# DevOps Info Service

Web service providing system information and health status via REST API.

## Requirements

- Python 3.11+
- pip

## Installation

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

## Usage

```bash
python app.py                      # Default: http://0.0.0.0:8000
PORT=3000 python app.py            # Custom port
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service and system information |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI documentation |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Port number |
| `DEBUG` | `false` | Enable auto-reload |

## Project Structure

```
app_python/
├── app.py              # Main application
├── requirements.txt    # Dependencies
├── README.md
├── tests/
└── docs/
    └── LAB01.md
```
