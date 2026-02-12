# Lab 3 - CI/CD

## 1. Overview

**Testing framework:** pytest
- Chosen for concise syntax, rich fixtures, and strong ecosystem support.

**Coverage scope:**
- `GET /` and `GET /health` responses (status + JSON shape)
- Error handling for `404` and `500`

**CI workflow triggers:**
- `push` and `pull_request` on `master`
- Path filters so CI runs only when `app_python/**` or workflow files change
- Docker publish runs only on SemVer tag pushes (`vX.Y.Z`)

**Versioning strategy:** SemVer
- Docker tags: `X.Y.Z`, `X.Y`, `X`, and `latest`
- Chosen for clear release semantics and breaking-change signaling

---

## 2. Workflow Evidence

- **Successful workflow run:**
  - https://github.com/mpasgat/DevOps-Core-Course/actions/workflows/python-ci.yml
- **Tests passing locally:**
  - Command: `pytest --cov=. --cov-report=term --cov-report=xml`
  - Paste terminal output here
- **Docker image on Docker Hub (Python):**
  - https://hub.docker.com/r/112005/devops-lab3-python
- **Docker image on Docker Hub (Java):**
  - https://hub.docker.com/r/112005/devops-lab3-java
- **Status badge in README:**
  - https://github.com/mpasgat/DevOps-Core-Course/actions/workflows/python-ci.yml

---

## 3. Best Practices Implemented

- **Dependency caching:** `actions/setup-python` pip cache speeds up installs.
- **Fail fast:** Jobs stop on first failing step to save time.
- **Job dependencies:** Docker publish depends on tests/lint passing.
- **Least privilege:** Workflow permissions limited to `contents: read`.
- **Concurrency control:** Cancel outdated runs for the same ref.
- **Conditional publishing:** Docker push only on tag releases.

**Caching impact:**
- Cache hit/miss timing noted in Actions logs (add before/after numbers).

**Snyk:**
- `snyk test --severity-threshold=high` runs when `SNYK_TOKEN` is present.
- Document any findings and remediation steps here.

---

## 4. Key Decisions

**Versioning Strategy:**
- SemVer tags align with release practices and make breaking changes explicit.

**Docker Tags:**
- `X.Y.Z`, `X.Y`, `X`, `latest` from the SemVer tag (`vX.Y.Z`).

**Workflow Triggers:**
- Push/PR on `master` with path filters to avoid unrelated CI runs.
- Docker publishing only on release tags to avoid accidental pushes.

**Test Coverage:**
- Covered: core endpoints and error handlers.
- Not covered: startup logging paths and environment-variable parsing.
- Threshold: `70%` enforced in CI.

---

## Bonus - Multi-App CI and Coverage

- **Java workflow:** .github/workflows/java-ci.yml runs Checkstyle, tests, and Docker publish.
- **Path filters:** Python CI triggers only for `app_python/**`, Java CI only for `app_java/**`.
- **Coverage badge:** Codecov badge added to `app_python/README.md`.

---

## 5. Challenges (Optional)

- Note any setup issues, token configuration, or CI failures here.
