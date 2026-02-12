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

- **Python CI run (tests):**
  - https://github.com/mpasgat/DevOps-Core-Course/actions/runs/21957867584/job/63426927143
- **Python CI run (docker):**
  - https://github.com/mpasgat/DevOps-Core-Course/actions/runs/21957867584/job/63426980301
- **Java CI run (tests):**
  - https://github.com/mpasgat/DevOps-Core-Course/actions/runs/21957867555/job/63426926927
- **Java CI run (docker):**
  - https://github.com/mpasgat/DevOps-Core-Course/actions/runs/21957867555/job/63426991945
- **Tests passing locally:**
  - Command: `ruff check .` + `pytest --cov=. --cov-report=term --cov-report=xml --cov-fail-under=70`
  - Output:
    ```
    All checks passed!
    =================================== test session starts ===================================
    platform win32 -- Python 3.12.4, pytest-9.0.2, pluggy-1.6.0
    rootdir: C:\Users\пк\OneDrive\Документы\GitHub\DevOps-Core-Course\app_python
    plugins: cov-7.0.0
    collected 4 items

    tests\test_app.py ....                                                               [100%]

    ===================================== tests coverage ======================================
    _____________________ coverage: platform win32, python 3.12.4-final-0 _____________________

    Name                Stmts   Miss  Cover
    ---------------------------------------
    app.py                 46      4    91%
    tests\__init__.py       0      0   100%
    tests\test_app.py      52      0   100%
    ---------------------------------------
    TOTAL                  98      4    96%
    Coverage XML written to file coverage.xml
    Required test coverage of 70% reached. Total coverage: 95.92%
    ==================================== 4 passed in 1.55s ====================================
    ```
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
- Cache enabled via `actions/setup-python` pip caching; cache hits visible in Actions logs on subsequent runs.

**Snyk:**
- `snyk test --severity-threshold=high --file=requirements.txt --package-manager=pip --skip-unresolved` runs when `SNYK_TOKEN` is present.
- Result (local):
  ```
  ✔ Tested 10 dependencies for known issues, no vulnerable paths found.
  ```
- Result (CI):
  ```
  ✔ Tested 9 dependencies for known issues, no vulnerable paths found.
  ```

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
