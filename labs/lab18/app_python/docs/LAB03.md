# Lab 3 — CI/CD, Automated Testing & Security

## Testing Framework Selection

I have selected Pytest as the main testing framework for this project due to its simplicity, powerful features, and wide adoption in the Python community. Pytest allows for easy test writing with minimal boilerplate, supports fixtures for setup and teardown, and provides rich reporting capabilities. Additionally, its extensive plugin ecosystem enables integration with various tools and frameworks, making it versatile for testing Python applications.

## Unit Testing

### Test Structure

* Tests are located in `app_python/tests/`
* Each endpoint has separate tests:

  * `test_root.py` — tests for `/`
  * `test_health.py` — tests for `/health`
* Each test verifies:

  * Status codes
  * Response structure
  * Required fields
  * Method restrictions (e.g., POST on `/health` returns 405)
  * Unknown endpoints return 404

### Running Tests Locally

```bash
pytest -v
```

### Terminal Output Showing All Tests Passed

```bash
(venv) gleb-pp@gleb-mac iu-devops-course % pytest -v            
================================================= test session starts ==================================================
platform darwin -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0 -- /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12
cachedir: .pytest_cache
rootdir: /Users/gleb-pp/Documents/InnoAssignments/S26 DevOps/iu-devops-course
plugins: anyio-4.12.1
collected 11 items                                                                                                     

app_python/tests/test_health.py::test_health_status_code PASSED                                                  [  9%]
app_python/tests/test_health.py::test_health_response_structure PASSED                                           [ 18%]
app_python/tests/test_health.py::test_health_method_not_allowed PASSED                                           [ 27%]
app_python/tests/test_health.py::test_unknown_endpoint PASSED                                                    [ 36%]
app_python/tests/test_root.py::test_root_status_code PASSED                                                      [ 45%]
app_python/tests/test_root.py::test_root_structure PASSED                                                        [ 54%]
app_python/tests/test_root.py::test_service_info_fields PASSED                                                   [ 63%]
app_python/tests/test_root.py::test_system_info_fields PASSED                                                    [ 72%]
app_python/tests/test_root.py::test_runtime_info_fields PASSED                                                   [ 81%]
app_python/tests/test_root.py::test_request_info_fields PASSED                                                   [ 90%]
app_python/tests/test_root.py::test_endpoints_info PASSED                                                        [100%]

============================================ 11 passed in 0.17s ============================================
```

## Code Quality

I use `ruff` for code style and formatting:

```bash
ruff check . --fix
All checks passed!
```

All issues were automatically fixed, ensuring consistent code style.

---

## CI/CD Workflow

**Workflow Name:** Python CI/CD for DevOps Info Service

**Implemented Steps:**

1. **Code Quality & Testing**

   * Install dependencies
   * Run linter (`ruff`)
   * Run unit tests (`pytest`)

2. **Docker Build & Push**

   * Authenticate with Docker Hub
   * Build Docker image
   * Tag images using **Semantic Versioning (SemVer)**:

     * `vMAJOR.MINOR.PATCH` → `1.0.0`
     * Also tag `latest`
   * Push images to Docker Hub

**Versioning Strategy:** Semantic Versioning (SemVer)

*Reason:* Traditional software releases with clear version increments (major, minor, patch). This ensures reproducibility and clarity for production deployment.

**Example Tags:**

* `glebpp/app_python:1.0.0`
* `glebpp/app_python:1.0`
* `glebpp/app_python:latest`

**Workflow Trigger:**
Runs on **push and pull_request** events for **all branches**, ensuring CI runs regardless of the branch.

---

## Dependency Caching

Caching Python dependencies improves workflow speed:

| Workflow        | Duration  |
| --------------- | --------- |
| Without caching | 8 seconds |
| With caching    | 7 seconds |

*Measured improvement:* ~12.5% faster execution.

---

## Security Scanning with Snyk

* Integrated Snyk into the CI workflow.
* Scans both Python dependencies and the Docker base image.
* Found vulnerabilities in the base image (`python:3.13-slim`) related to glibc and tar:

  * Severity: Low / Minor
  * No known exploit
  * No remediation path available (depends on upstream Debian patches)

**Mitigation Actions:**

* Used a stable Python base image
* Ensured regular security scanning in CI
* Verified that application code and dependencies contain no critical vulnerabilities

---

## CI Best Practices Applied

1. **Status Badge**

   * Added a GitHub Actions badge to `README.md` to show workflow status (passing/failing).
   
   ![CI Status](https://github.com/gleb-pp/iu-devops-course/actions/workflows/python-ci.yml/badge.svg)

2. **Dependency Caching**

   * Implemented caching for Python dependencies, reducing CI run time.

3. **Consistent Docker Tagging**

   * Used SemVer + `latest` tag strategy for clarity and reproducibility.

4. **Workflow Triggering on All Branches**

   * Ensures tests run on feature, development, and main branches to catch bugs early.

5. **Automated Security Scans**

   * Integrated Snyk to detect vulnerabilities in dependencies and base images.
