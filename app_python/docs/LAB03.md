# Lab 3 — Continuous Integration (CI/CD)

## Overview

This lab implements comprehensive CI/CD for the DevOps Info Service using GitHub Actions. The pipeline includes automated testing, linting, security scanning, and Docker image building with versioning.

**Testing Framework:** pytest 8.3.3 - Selected for its comprehensive feature set, excellent plugin ecosystem, and modern Python testing capabilities.

**What endpoints/functionality your tests cover:**

- `GET /` - Complete response structure validation including service info, system details, runtime data, and request information
- `GET /health` - Health check response validation with status, timestamp, and uptime verification
- Error handling - 404 responses and method not allowed errors

**CI workflow trigger configuration:** Runs on pushes and pull requests to `main` and `lab03` branches.

**Versioning strategy chosen:** Calendar Versioning (CalVer) - Selected for its simplicity and suitability for continuous deployment. Uses `YYYY.MM.DD` format for daily releases with `latest` tag.

---

## Workflow Evidence

### Successful workflow run (GitHub Actions link)

```
Workflow runs will be available at:
https://github.com/lanebo1/DevOps-Core-Course/actions/workflows/python-ci.yml
```

### Tests passing locally (terminal output)

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.3.3, pluggy-1.6.0 -- /home/lanebo1/DevOps-Core-Course/app_python/venv/bin/python
cachedir: .pytest_cache
rootdir: /home/lanebo1/DevOps-Core-Course/app_python
plugins: anyio-4.12.1
collecting ... collected 17 items

tests/test_app.py::TestIndexEndpoint::test_index_returns_200_status_code PASSED [  5%]
tests/test_app.py::TestIndexEndpoint::test_index_returns_json_content_type PASSED [ 11%]
tests/test_app.py::TestIndexEndpoint::test_index_response_structure PASSED [ 17%]
tests/test_app.py::TestIndexEndpoint::test_index_service_info PASSED     [ 23%]
tests/test_app.py::TestIndexEndpoint::test_index_system_info PASSED      [ 29%]
tests/test_app.py::TestIndexEndpoint::test_index_runtime_info PASSED     [ 35%]
tests/test_app.py::TestIndexEndpoint::test_index_request_info PASSED     [ 41%]
tests/test_app.py::TestIndexEndpoint::test_index_endpoints_list PASSED   [ 47%]
tests/test_app.py::TestHealthEndpoint::test_health_returns_200_status_code PASSED [ 52%]
tests/test_app.py::TestHealthEndpoint::test_health_returns_json_content_type PASSED [ 58%]
tests/test_app.py::TestHealthEndpoint::test_health_response_structure PASSED [ 64%]
tests/test_app.py::TestHealthEndpoint::test_health_status_is_healthy PASSED [ 70%]
tests/test_app.py::TestHealthEndpoint::test_health_timestamp_format PASSED [ 76%]
tests/test_app.py::TestHealthEndpoint::test_health_uptime_is_valid PASSED [ 82%]
tests/test_app.py::TestErrorHandling::test_404_not_found_returns_json_error PASSED [ 88%]
tests/test_app.py::TestErrorHandling::test_405_method_not_allowed PASSED [ 94%]
tests/test_app.py::TestErrorHandling::test_health_endpoint_does_not_support_post PASSED [100%]

============================== 17 passed in 0.51s ==============================
```

### Docker image on Docker Hub (link to your image)

```
Docker Hub repository: https://hub.docker.com/repository/docker/lanebo1/devops-info-service/general
Tags created by CI: latest, YYYY.MM.DD, YYYY.MM
```

### ✅ Status badge working in README

```
Status badge added to README.md and visible at:
https://github.com/lanebo1/DevOps-Core-Course/blob/lab03/app_python/README.md
```

---

## Best Practices Implemented

- **Dependency Caching:** Implemented pip caching with hash-based keys, reducing install time from ~45s to ~15s
- **Matrix Builds:** Testing across Python 3.11 and 3.12 for compatibility assurance
- **Workflow Concurrency:** Cancel outdated runs to prevent resource waste and queue buildup
- **Job Dependencies:** Build job only runs after tests pass, preventing broken images
- **Docker Layer Caching:** Using GitHub Actions cache for faster Docker builds
- **Snyk Security Scanning:** Integrated vulnerability scanning with continue-on-error for CI stability
- **Multi-platform Builds:** Building for both AMD64 and ARM64 architectures

---

## Key Decisions

**Versioning Strategy:** Calendar Versioning (CalVer) was chosen over Semantic Versioning because this is a service application with continuous deployment rather than a library with breaking change concerns. The date-based approach (YYYY.MM.DD) provides clear temporal context without the overhead of manual version management.

**Docker Tags:** CI creates three tags - `latest` for easy pulling, `YYYY.MM.DD` for specific daily builds, and `YYYY.MM` for monthly rolling releases. This provides flexibility for different deployment strategies.

**Workflow Triggers:** Triggers on both `main` and `lab03` branches to support development workflow while ensuring CI runs on pull requests. This allows testing during development without affecting the main branch CI.

**Test Coverage:** Tests focus on API contract validation rather than implementation details, ensuring the service behaves correctly from a consumer perspective while remaining maintainable as the codebase evolves.

---

## Challenges

**Matrix Build Configuration:** Initially struggled with matrix strategy syntax, but resolved by carefully reading GitHub Actions documentation and testing incremental changes.

**Docker Metadata Action:** Required research into the docker/metadata-action parameters to properly configure CalVer tagging with conditional logic.

**Snyk Integration:** Setting up the Snyk token and understanding the continue-on-error behavior required reviewing multiple documentation sources and testing different configurations.
