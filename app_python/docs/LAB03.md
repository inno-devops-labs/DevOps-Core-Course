## 1. Overview

- **Testing framework:** `pytest` with `pytest-cov` for coverage. Pytest was chosen for its simple, expressive syntax, rich plugin ecosystem, and excellent support for testing Flask apps with a built-in test client.
- **Endpoints covered by tests:**
  - `GET /` – happy path, response structure and types, request metadata, and advertised endpoints list.
  - `GET /health` – happy path, status, uptime and timestamp format.
  - Error paths:
    - `GET /does-not-exist` – 404 JSON error handler.
    - Forced internal error in `/` – 500 JSON error handler.
    - `POST /` – method-not-allowed behaviour.
- **CI workflow triggers:**
  - Runs on `push` and `pull_request` to `master` and `lab*` branches.
  - Only triggers when files under `app_python/**` or the workflow file itself change.
- **Versioning strategy:** **CalVer (Calendar Versioning)** using `YYYY.MM.DD`, generated at build time inside the CI workflow. CalVer matches a continuous-delivery style for this service, where release frequency is tied to the date rather than explicit breaking-change semantics.

---

## 2. Workflow Evidence




- ✅ Successful workflow run (GitHub Actions link):
  https://github.com/Rash1d1/DevOps-Core-Course/actions/runs/21961633075

- ✅ Tests passing locally (terminal output):
```bash
  $ cd app_python
  $ pytest  
================================== test session starts ==================================
platform linux -- Python 3.12.3, pytest-8.3.4, pluggy-1.6.0
rootdir: /home/j0cos/innopolis/Devops/DevOps-Core-Course/app_python
plugins: cov-6.0.0
collected 5 items                                                                       

tests/test_app.py .....                                                           [100%]

=================================== 5 passed in 0.20s ===================================
```
- ✅ Docker image on Docker Hub:
  https://hub.docker.com/repository/docker/j0cos/devops-info-service/tags/2026.02.12/sha256-3a83b9cf2b7463c71e5b44fb103d9777704b9c4fb70e0bf8a7b47cb1c4a62149

- ✅ Status badge working in README:
  See screenshots folder
  


---

## 3. Best Practices Implemented

- **Practice 1 – Matrix builds:** The `Python CI` workflow tests against multiple Python versions (`3.11` and `3.12`), increasing confidence that the app and dependencies behave consistently across supported runtimes.
- **Practice 2 – Fail-fast with job dependencies:** Docker build/push and Snyk scanning depend on the lint/test job, so no images are published and no security scan is run if tests fail.
- **Practice 3 – Conditional deployment:** Docker images are only built and pushed when the `master` branch is updated, preventing feature branches from publishing release images.
- **Practice 4 – Concurrency control:** Workflows use a concurrency group per ref with `cancel-in-progress: true`, so outdated runs are cancelled when new commits are pushed to the same branch.
- **Caching:** `actions/setup-python`'s pip cache is enabled with `cache: pip` and `cache-dependency-path: app_python/requirements.txt`. The first run installs dependencies from scratch; subsequent runs reuse the cache and should be noticeably faster (often cutting dependency installation time from tens of seconds to just a few seconds).
- **Snyk:** The `security-scan` job uses `snyk/actions/python-3.12@master` against `app_python/requirements.txt` with a `medium` severity threshold, uploading SARIF results to GitHub’s Security tab. After you configure `SNYK_TOKEN`, the job will report any known vulnerable dependencies.

Pipeline first run: 1m7s
Second and othes runs: less than 30s

---

## 4. Key Decisions

- **Versioning Strategy:** CalVer (`YYYY.MM.DD`) was chosen because this service behaves like a continuously deployed application. The date-based version makes it easy to see when an image was produced and works well when breaking-change semantics are less critical than recency.
- **Docker Tags:** Each CI run on `master` produces at least two tags for the Python app:
  - `devops-info-service:<calver>` (e.g., `2026.02.12`)
  - `devops-info-service:latest`
  Additional tags (such as branch-specific tags) can be added later if needed.
- **Workflow Triggers:** The workflow is limited to changes in `app_python/**` (plus the workflow file) to avoid unnecessary runs when unrelated files are modified. `push` and `pull_request` events on `master` and lab branches ensure both direct commits and PRs are validated.
- **Test Coverage:** Unit tests focus on the externally visible behaviour of the HTTP endpoints (status codes, JSON structure, timestamps, and error handling) rather than internal implementation details. Non-critical glue code (such as the `__main__` block that starts the Flask server) is intentionally not exercised in tests.

---
