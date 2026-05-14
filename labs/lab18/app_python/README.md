````markdown
# DevOps Info Service

![CI](https://github.com/qobz1e/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)

## Run locally

```bash
python app.py
````

## Run tests

```bash
cd app_python
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest -v
```

## Run with coverage

```bash
pytest --cov=app --cov-report=term
```