# Lab 3 — Continuous Integration (CI/CD)

## 1. Overview

### Testing framework choice
- **Framework**: `pytest`
- **Why**: concise assertions, great Flask testing story via built-in test client, strong ecosystem.

### What the tests cover
- `GET /`: response JSON structure and key fields
- `GET /health`: healthy response payload
- **Error cases**:
  - `GET /does-not-exist` → JSON 404
  - forced internal failure → JSON 500

### CI workflow triggers
- Runs on **push** and **pull_request** when files under `app_python/**` (or the workflow) change.

### Versioning strategy
- **Strategy**: CalVer
- **Format**: `YYYY.MM.<run_number>`
- **Tags pushed**: version tag + `latest`

---

## 2. Workflow Evidence

- ✅ **Successful workflow run**: <https://github.com/ilyalinhnguyen/DevOps-Core-Course/actions/runs/21859948877>
- ✅ **Tests passing locally**:

```text
===================================================================================== test session starts ======================================================================================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/linh/Innopolis/DevOps-Core-Course/app_python
collected 4 items                                                                                                                                                                              

tests/test_endpoints.py ....                                                                                                                                                             [100%]

====================================================================================== 4 passed in 0.05s =======================================================================================
```

- ✅ **Docker Hub image**: <https://hub.docker.com/repository/docker/pickpusha/devops-info-service-python/tags/2026.02.1/sha256-17c76458436045cab8940ba0bc4efda3d3a40db7e84d4988b95582cd3ca77f2d>
- ✅ **Status badge visible**: Go to [README.md](/app_python/README.md)

---

## 3. Best Practices Implemented

- **Fail fast**: tests must pass before docker build/push runs.
- **Path filters**: CI only runs when `app_python/**` changes.
- **Least privilege**: explicit workflow permissions.
- **Concurrency**: cancel outdated runs on the same branch.
- **Caching**: pip dependency cache enabled for faster runs.
- **Snyk**: dependency vulnerability scan (fails build on high severity).

### Caching metrics
- Before: 2 min 34 seconds
- After: 1 min 4 seconds

### Snyk results
- Vulnerabilities found: no
- Actions taken: none

---

## 4. Key Decisions

### Versioning Strategy
Chose **CalVer** because this is a continuously delivered service where release cadence matters more than API break indicators.

### Docker Tags
CI produces:
- `DOCKERHUB_USERNAME/devops-info-service-python:<YYYY.MM.run>` (version)
- `DOCKERHUB_USERNAME/devops-info-service-python:latest`

### Workflow Triggers
Run on PRs to validate changes early, and only push images on `master` and `lab03` (`lab03` for showing the working pipeline) pushes to avoid publishing images from unmerged code.

### Test Coverage
Covered: main endpoints and error handlers.
Not covered (if any): nothing.

---
