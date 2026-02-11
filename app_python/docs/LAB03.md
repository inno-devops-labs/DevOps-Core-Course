# LAB03 - Continuous Integration (Python)

## 1. Overview

- Testing framework: **pytest**.
  - Reason: concise syntax, strong fixtures (`monkeypatch`), and mature ecosystem for API testing.
- Covered functionality:
  - `GET /` success case, response schema and endpoint list.
  - `GET /` request metadata behavior (`X-Forwarded-For`, `User-Agent`).
  - `GET /health` success case.
  - Error handling: custom `404` and generic `500` JSON responses.
- CI triggers:
  - `push` and `pull_request` for `main`/`master`.
  - Path filters: workflow runs only when `app_python/**` or `.github/workflows/python-ci.yml` changes.
  - Manual trigger via `workflow_dispatch`.
- Versioning strategy: **CalVer (`YYYY.MM.DD`)**.
  - Chosen because the service is release-frequency oriented and date tags are easy to map to deployment day.

## 2. Workflow Evidence

- Workflow page:
  - https://github.com/Vlad1mirZhidkov/DevOps-Core-Course/actions/workflows/python-ci.yml
- Actions runs:
  - https://github.com/Vlad1mirZhidkov/DevOps-Core-Course/actions
- Docker image repository:
  - https://hub.docker.com/r/vladimirzhidkov/devops-info-service
- README with status badges:
  - https://github.com/Vlad1mirZhidkov/DevOps-Core-Course/tree/master/app_python#readme

Local test command:
```bash
pytest app_python/tests --cov=app_python --cov-report=term-missing --cov-report=xml --cov-fail-under=70
```

Local verification result:
- `python -m ruff check app_python` -> `All checks passed!`
- `python -m pytest app_python/tests --cov=app_python --cov-report=term-missing --cov-report=xml --cov-fail-under=70` -> `6 passed`, total coverage `92.26%`.

## 3. Best Practices Implemented

- **Fail fast with job dependencies**
  - `docker` job depends on `test`, so image build/push never happens when lint/tests fail.
- **Conditional deployment**
  - Docker publish runs only for `push` events on `main`/`master`, not on pull requests.
- **Concurrency control**
  - New commits cancel outdated runs on the same ref to reduce queue time and cloud spend.
- **Dependency caching**
  - `actions/setup-python` pip cache is enabled with `requirements.txt` and `requirements-dev.txt` as cache keys.
- **Least-privilege permissions**
  - Workflow-level `permissions: contents: read` limits token scope.
- **Docker layer caching**
  - Buildx + GHA cache (`cache-from/cache-to`) reduce rebuild time when app dependencies are unchanged.
- **Security scanning**
  - Snyk scan is integrated with `--severity-threshold=high` and enabled when `SNYK_TOKEN` is provided.
- **Coverage quality gate**
  - `--cov-fail-under=70` prevents silent test-quality regressions.

Caching observation approach:
- Baseline (cold cache): first run after dependency or Docker layer cache miss.
- Optimized (warm cache): subsequent run with unchanged dependency manifests.
- Compare `Install dependencies` and Docker build step durations in Actions logs.

Snyk handling policy:
- Build fails on high/critical dependency vulnerabilities when Snyk is enabled.
- Vulnerabilities are fixed by dependency upgrades or documented risk acceptance if no fix exists.

## 4. Key Decisions

- **Versioning Strategy**
  - CalVer was selected over SemVer to keep release automation simple and date-oriented.
  - For service deployments, release date traceability is more valuable than API-change semantics.

- **Docker Tags**
  - The pipeline pushes two tags: `YYYY.MM.DD` and `latest`.
  - Date tag provides immutable release reference; `latest` is convenient for quick pull/testing.

- **Workflow Triggers**
  - `push` + `pull_request` provide branch safety and pre-merge validation.
  - Path filters keep monorepo CI efficient by avoiding Python pipeline runs on unrelated changes.

- **Test Coverage**
  - Coverage focuses on public API behavior and error contracts.
  - Internal implementation details like logging format are intentionally not hard-asserted to reduce brittle tests.

## 5. Challenges

- No blockers after local environment setup; lint and tests pass with coverage above threshold.
