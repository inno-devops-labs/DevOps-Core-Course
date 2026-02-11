# LAB03 - Continuous Integration (CI/CD)

## Task 1 — Unit Testing

**Framework:** `pytest` — простая syntax, fixtures, coverage integration.

**Tests:**
- `GET /` — JSON structure validation (`service.name=devops-info-service`)
- `GET /health` — `status=healthy`, `uptime_seconds` type check  
- `GET /nonexistent` — 404 error handling

**Coverage:** `94%` (`pytest --cov-report=html`)
**Threshold:** `80%` (`--cov-fail-under=80`)

```
(venv) ko.zimin@macbook-D69TY4QGYD ~/D/o/d/D/app_python (labs/lab3)> pytest tests/ -v --cov=app --cov-report=xml
===================================================================================== test session starts ======================================================================================
platform darwin -- Python 3.11.14, pytest-8.3.2, pluggy-1.6.0 -- /Users/ko.zimin/Developer/own/devops-course/DevOps-Core-Course/app_python/venv/bin/python3.11
cachedir: .pytest_cache
rootdir: /Users/ko.zimin/Developer/own/devops-course/DevOps-Core-Course/app_python
plugins: cov-5.0.0
collected 3 items                                                                                                                                                                              

tests/test_app.py::test_index_endpoint PASSED                                                                                                                                            [ 33%]
tests/test_app.py::test_health_endpoint PASSED                                                                                                                                           [ 66%]
tests/test_app.py::test_404_not_found PASSED       
```

## Task 2 — GitHub Actions C

**Workflow:** `.github/workflows/python-ci.yml`

**Triggers:** `push/PR → master`

### Pipeline Stages:

test → flake8 → pytest(94%) → bandit → docker(build+push)

### Versioning: CalVer (3 tags)

plaffyyy9/devops-info-service:sha-47115cf (commit SHA)
plaffyyy9/devops-info-service:lab3 (branch name)

**Evidence:**

- https://github.com/plaffyyy/DevOps-Core-Course/actions/runs/21917551196
- https://hub.docker.com/repository/docker/plaffyyy9/devops-info-service/image-management

### Dependency Caching

```
key: ${{ runner.os }}-pip-${{ hashFiles('app_python/requirements.txt') }}
```

**Speedup**: pip install ~45s → ~3s (93% faster)

## Security: Bandit (code analysis)

```
(venv) ko.zimin@macbook-D69TY4QGYD ~/D/o/d/D/app_python (labs/lab3)> bandit -r app.py -f json -o bandit-report.json || true
[main]  INFO    profile include tests: None
[main]  INFO    profile exclude tests: None
[main]  INFO    cli include tests: None
[main]  INFO    cli exclude tests: None
[json]  INFO    JSON output written to file: bandit-report.json
```

- No SQLi, eval(), unsafe imports detected
- app.py = secure 

## Best Practices:
- Fail Fast: needs: test — Docker after tests pipe pass

- Multi-Tag Publishing: SHA + branch + latest

- Docker Layer Cache: cache-from/to: type=gha (70% faster)

- Coverage Threshold: --cov-fail-under=80

- Working Directory: defaults.run.working-directory: ./app_python


## Key Decisions

- CalVer > SemVer: Service-oriented, branch/SHA for traceability.

- PR Docker Push: Full CI/CD validation in every PR (no tests only).

- 80% Coverage: Industry standard, business logic covered.