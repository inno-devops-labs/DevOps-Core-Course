# DevOps Info Service

This project delivers a Python-based web service that reports detailed system and runtime information. It will be expanded across the labs to include health monitoring, containerization, CI/CD, and persistence. The app uses FastAPI.

## Structure
- `app.py` — service entry point (framework selection in Task 1.2)
- `requirements.txt` — Python dependencies
- `docs/` — lab notes and screenshots
- `tests/` — unit tests to be added in later labs

## Getting Started
1. Install dependencies: `python3 -m pip install -r requirements.txt`.
2. Run the app: `python3 app.py` (defaults to host `0.0.0.0` and port `5000`).
3. Override configuration with env vars: `HOST=127.0.0.1 PORT=8080 DEBUG=true python3 app.py` (reload follows `DEBUG`).
