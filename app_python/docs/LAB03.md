# Lab 03 — Continuous Integration & Automation

## 1. Testing Strategy & Framework

### Framework Selection: pytest

The testing framework **pytest** was chosen over alternatives (unittest, nose) for the following reasons:

- **Modern Pythonic syntax**: Uses simple `assert` statements instead of verbose `assertEqual()` methods
- **Powerful fixtures**: Clean test setup/teardown and dependency injection
- **FastAPI integration**: Works seamlessly with FastAPI's TestClient without server startup
- **Plugin ecosystem**: Excellent support for coverage, parallel execution, and reporting
- **Industry standard**: Most widely used in modern Python projects

### Test Coverage

4 tests were made to test both existing endpoints and error handling at invalid endpoint covering most of service functionality

### Test Execution

```bash
$ pytest app_python/tests/pytest.py -v
=============================================================================================== test session starts ================================================================================================
...
app_python/tests/pytest.py::test_index_endpoint PASSED                                                                                                                                                       [ 25%]
app_python/tests/pytest.py::test_health_endpoint PASSED                                                                                                                                                      [ 50%]
app_python/tests/pytest.py::test_404_not_found PASSED                                                                                                                                                        [ 75%]
app_python/tests/pytest.py::test_iso_utc_z PASSED                                                                                                                                                            [100%]

================================================================================================ 4 passed in 0.10s =================================================================================================
```

---

## 2. GitHub Actions CI Pipeline

### Workflow File Location

`.github/workflows/python-ci.yml`

### Workflow Architecture

**3 Jobs with smart dependencies:**

1. **Test and Lint** (ubuntu-latest)
   - Python 3.13 setup with pip caching
   - Install dependencies + flake8 + pytest
   - Run flake8
   - Run pytest

2. **Security Scan** (runs in parallel)
   - Snyk vulnerability scanning
   - Check only for HIGH/CRITICAL CVEs
   - Report if any dependencies failed

3. **Docker Build and Push** (depends on both previous jobs)
   - Authenticate to Docker Hub
   - Build image with caching
   - Tag and push

### Trigger Configuration

```yaml
on:
  push:
    branches: [master, main, lab03]
    paths: ['app_python/**', '.github/workflows/python-ci.yml']
  pull_request:
    branches: [master, main]
    paths: ['app_python/**', '.github/workflows/python-ci.yml']
```

**Rationale**: Path filtering prevents unnecessary runs on documentation changes.

### Docker Image Versioning

**Strategy**: SemVer versioning

**Why SemVer over CalVer?**
- Carries more information about changes than CalVer
- Am assuming rare updates for this software

**Tags per image**:
- `latest` - Points to most recent build
- `1.0.0` - SemVer tag

---

## 3. CI Best Practices & Optimizations

### Practice 1: Status Badge

Added to `app_python/README.md`:

[![Python CI](https://github.com/saddogsec/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](...)

Provides real-time visibility of pipeline status (passing/failing).

### Practice 2: Dependency Caching

Caching and requirements-dev.txt used to decrease pipeline execution time 

```yaml
cache: 'pip'
cache-dependency-path: |
  app_python/requirements.txt
  app_python/requirements-dev.txt
```

### Practice 3: Security Scanning with Snyk

Dedicated job scans `requirements.txt` for vulnerabilities:

```yaml
- name: Run Snyk to check for vulnerabilities
          env:
            SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
          run: snyk test --package-manager=pip --file=requirements.txt --severity-threshold=high
```

### Practice 4: Parallel Job Execution

Test and security jobs run in parallel instead of sequentially considerably decreasing pipeline execution time.

### Practice 5: Job Dependencies with Fail-Fast

```yaml
docker:
  needs: [test, security]
  if: github.ref == 'refs/heads/master'
```

### Practice 6: Secure secret management
Github secrets is used instead of .env or other vulnerable ways to store SNYK_TOKEN and DOCKER_TOKEN
```yaml
env:
            SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
...
with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
```
---

## 4. Technical Analysis

### Why This Pipeline Works
It uses standart approach, with multiple parallel tests which all needs to pass before creating deployment artifact
```
Push → Tests pass? and Security scan completes? → Docker build & push
         (required)      (required)           (only on relevant branches)
```

### Layer Caching Impact

Docker layers are cached by GitHub Actions. On subsequent runs:
- Base image: reused
- Dependencies: reused (if requirements.txt unchanged)
- Application code: rebuilt (changed)
- **Result**: faster builds

## 5. Key Decisions & Rationale

### Decision 1: CalVer vs SemVer Versioning

**Chosen**: SemVer versioning

**Why SemVer over CalVer?**
- Easy to identify whenever something important changed

---

### Decision 2: Snyk Severity Threshold

**Chosen**: HIGH (fail only on HIGH/CRITICAL)

**Rationale**:
- MEDIUM/LOW issues are hard to exploit in this software, so they seem irrelevant
- Considering Low issues would extremely limit amount of available libraries to use

---

## 6. Challenges & Solutions
No challenges were present during the lab
