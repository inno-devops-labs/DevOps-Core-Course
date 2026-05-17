# DevOps Python Application

![Python CI/CD Pipeline](https://github.com/nadiaa02/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab03)

## Prerequisites
- Python 3.11+

## Installation
`bash
pip install -r requirements.txt
`

## Development
`bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov=.
`

## Docker
`bash
docker pull nadiaa02/devops-python-app:latest
docker run -p 5000:5000 nadiaa02/devops-python-app:latest
`

## CI/CD Pipeline
- **Testing**: pytest with coverage
- **Linting**: flake8
- **Security**: Snyk vulnerability scanning
- **Versioning**: Calendar Versioning (CalVer)
- **Deployment**: Automatic Docker build & push