# Continuous Integration

## Overview

This project uses GitHub Actions to run automated checks for the Python web application.

The CI workflow runs on push and pull request events when files inside the `app_python` directory or the workflow file are changed.

## Workflow Steps

The workflow includes the following stages:

1. Checkout repository.
2. Set up Python.
3. Install dependencies.
4. Run linter.
5. Run unit tests.
6. Run Snyk vulnerability checks.
7. Set up Docker Buildx.
8. Login to Docker Hub.
9. Build and push Docker image.

## CI Best Practices Used

### Explicit Python Version

The workflow uses a fixed Python version to make builds reproducible.

### Dependency Caching

The workflow uses pip cache to speed up dependency installation.

### Docker Build Cache

Docker Buildx cache is used to speed up repeated image builds.

### Separate Test and Docker Jobs

The Docker image is built only after the test job has completed successfully.

### Path Filters

The workflow runs only when files in the `app_python` directory or the workflow file itself are changed.

### Secrets

Docker Hub credentials and the Snyk token are stored in GitHub Actions secrets.

Used secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `SNYK_TOKEN`

### Pull Request Validation

The workflow runs on pull requests to validate code before merging.

### Linting

Ruff is used to check code quality before tests and Docker publishing.

## Snyk

Snyk is used to check Python dependencies for known vulnerabilities.

The workflow fails if Snyk finds vulnerabilities with high severity or higher.
