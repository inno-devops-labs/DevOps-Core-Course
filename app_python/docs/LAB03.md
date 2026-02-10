# Lab 3 — Continuous Integration (CI/CD)

## Task 1

Testing framework choice and why:
Pytest. It has concise assertions, excellent fixtures for Flask test clients, and a large plugin ecosystem. It keeps tests readable while still supporting more advanced scenarios like monkeypatching error paths.

Test structure explanation:
Tests live in `app_python/tests/test_app.py`. A `client` fixture builds a Flask test client. The suite covers:
- `GET /` JSON shape, required fields, and basic type checks.
- `GET /health` success response and timestamp format.
- 404 error handler response for unknown routes.
- 500 error handler response by forcing a runtime exception.

How to run tests locally:
```bash
cd app_python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

Terminal output showing all tests passing:
```text
============================= test session starts ==============================
platform darwin -- Python 3.14.0, pytest-8.3.4, pluggy-1.6.0
rootdir: /Users/igor/inno/DevOps-Core-Course
collected 4 items

app_python/tests/test_app.py ....                                        [100%]

============================== 4 passed in 0.13s ===============================
```

## Task 2

Workflow trigger strategy and reasoning:
Run on pull requests to `main`/`master` for fast feedback without publishing images, and on pushes to `main`/`master` for continuous validation. Docker build and push only runs on SemVer tag pushes (`v*.*.*`) to avoid publishing images for unversioned commits.

Why I chose specific GitHub Actions:
- `actions/checkout`: standard, reliable repo checkout.
- `actions/setup-python`: official Python toolchain setup and caching support.
- `docker/login-action`: secure, official Docker Hub authentication.
- `docker/metadata-action`: automatic SemVer-derived tags without custom scripting.
- `docker/build-push-action`: official Buildx build and push with multi-tag support.

Docker tagging strategy:
Semantic Versioning (SemVer) based on git tags. On tag `v1.2.3`, the workflow pushes:
- `username/devops-info-service:1.2.3`
- `username/devops-info-service:1.2`
- `username/devops-info-service:latest`

Link to successful workflow run in GitHub Actions tab:
```text
https://github.com/chomosuce/DevOps-Core-Course/actions/runs/21857206785/job/63076772951
```

Screenshot of green checkmark docs/screenshots/checkmark

## Task 3

Status badge in README:
- Added badge at the top of `app_python/README.md`.

Caching implementation and speed improvement metrics:
- Implemented pip cache via `actions/setup-python` with `cache: pip`.
- Cache keys include `app_python/requirements.txt` and `app_python/requirements-dev.txt`.
- Speed improvement (fill after first cached run):
  - First run (cold cache): `<fill>` seconds for install step.
  - Second run (warm cache): `<fill>` seconds for install step.
  - Improvement: `<fill>` seconds (~`<fill>%`).

Snyk integration results and vulnerability handling:
- Added Snyk scan step using `snyk/actions/python@v3` with `SNYK_TOKEN` secret.
- Snyk runs on the test job after dependency install.
- Findings:
  - `<fill: none found>` or `<list vulnerabilities>`
- Mitigation:
  - `<fill: upgraded package X to Y>` or `N/A`.

CI best practices applied and why they matter:
- Minimal permissions (`contents: read`) to reduce token scope.
- Concurrency with `cancel-in-progress` to avoid wasted CI minutes on outdated commits.
- Job timeouts to prevent hung workflows.
- Release-only Docker pushes on SemVer tags to avoid pushing unversioned images.

Terminal output showing improved workflow performance:
```text
<paste log snippet showing cached pip install and shorter duration>
```
