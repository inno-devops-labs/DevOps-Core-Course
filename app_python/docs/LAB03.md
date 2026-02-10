# Lab 03

## 1. Overview

### Testing Framework

* **Framework Chosen:** pytest
* **Rationale:** pytest was chosen for its simple syntax, powerful fixtures, and native integration with many CI tools.
* **Coverage:** My tests cover the following:
* `GET /`: Validates JSON structure, status code 200, and required fields.
* `GET /health`: Verifies the health check response and uptime increments
* `GET /unknown`: Verifies 404 response


### CI Workflow Configuration

* **Trigger Strategy:** The workflow is triggered on:
* `push` to the `main` branch.


* **Versioning Strategy:** SemVer
* **Rationale:** SemVer was chosen because it clearly communicates breaking changes to users of the Docker image.

---

## 2. Workflow Evidence

| Requirement | Evidence/Link |
| --- | --- |
| **Successful Workflow Run** | [Link to GitHub Actions Run](https://github.com/BulatGazizov-dev/DevOps-Core-Course/actions/runs/21883844379) |
| **Docker Hub Image** | [Link to Docker Hub Repository](https://hub.docker.com/r/bulatgazizov/python_app) |

### Local Terminal Output

```text
================================================================== test session starts ===================================================================
platform linux -- Python 3.13.9, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/bulatgazizov/Projects/DevOps-Core-Course/app_python
plugins: anyio-4.9.0
collected 4 items                                                                                                                                        

tests/test_main.py ....                                                                                                                            [100%]

=================================================================== 4 passed in 1.62s ====================================================================
```

---

## 3. Best Practices Implemented

* **Linting:** Integrated `flake8` to ensure code style consistency.
* **Caching:** Implemented `actions/setup-python` caching.
* **Snyk Security:** Integrated Snyk vulnerability scanning. >> Tested 55 dependencies for known issues, no vulnerable paths found.

* **Docker Metadata:** Used `docker/metadata-action` for automated, multi-tag management.

---

## 4. Key Decisions

**Versioning Strategy:**
I chose SemVer because it clearly says whether an update contains bug fixes (patch), new features (minor), or breaking changes (major).

**Docker Tags:**
My CI generates the following tags:

* `latest`: Always points to the most recent build
* `vX.Y.Z`: Specific semantic versions based on Git tags.

**Workflow Triggers:**
The workflow triggers on pushes to main or any other branch. This ensures all code is linted, tested, and scanned for vulnerabilities before integration.

**Test coverage:**
* `GET /`: Validates JSON structure, status code 200, and required fields.
* `GET /health`: Verifies the health check response and uptime increments
* `GET /unknown`: Verifies 404 response
