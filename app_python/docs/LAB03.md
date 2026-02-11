# LAB 03 — Testing & Coverage (Python)
## Objective

Implement automated testing and coverage reporting for the Python service (app_python) using:

* pytest

* pytest-cov

* Coverage threshold enforcement

* GitHub Actions CI

## Project Structure
```
DevOps-Core-Course/
│
├── .github/
│   └── workflows/
│       └── python-ci.yml
│
├── app_python/
│   ├── app.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   └── tests/
│       └── test_app.py
│
├── app_go/
│
└── LAB03.md
```
## Local Testing

Activate virtual environment:
```bash
cd app_python
venv\Scripts\activate
```
Install dependencies:
```bash
python -m pip install -r requirements-dev.txt
```
Run tests:
```bash
pytest -v
```

Coverage is enforced via pytest.ini.

## pytest.ini Configuration
```
[pytest]
addopts = --cov=. --cov-fail-under=70
```
This ensures:

* Coverage is calculated for the entire app

* Build fails if coverage is below 70%

## CI Pipeline (GitHub Actions)

Workflow file:
```
.github/workflows/python-ci.yml
```
**Trigger**

* Push to main

* Pull request to main

* Changes inside `app_python/**`

**Pipeline Steps**

1. Checkout code

2. Setup Python

3. Install dependencies

4. Run pytest with coverage

5. Fail if coverage < 70%