# lab 03: continuous integration (ci/cd)

## overview

### testing framework: pytest

i chose **pytest** for unit testing due to:

1. simple syntax: tests are written using plain python functions with assert statements - no need for test classes or special methods like in unittest.

2. powerful fixtures: pytest's fixture system provides flexible test setup/teardown, allowing shared test context and dependency injection.

3. excellent plugin ecosystem: wide range of plugins available including `pytest-cov` for coverage reporting.

4. industry standard: pytest is the de facto choice for modern python projects, making it easier for others to contribute.

### test coverage

tests cover both endpoints:
- `GET /` - validates complete JSON structure, all required fields, data types, and error cases
- `GET /health` - validates health status, timestamp, and uptime fields

### ci workflow configuration

the workflow triggers on **any push and pull request**, ensuring code quality is checked continuously across all branches.

### versioning strategy: semantic versioning (semver)

i chose semver for docker image tagging:
- format: `major.minor.patch` (e.g., `1.0.0`)
- tags: full version, minor version, `latest`, and commit sha
- when to use: traditional software releases where breaking changes need explicit communication

semver provides clear signals about api compatibility changes, which is important for services consumed by other applications.

## workflow evidence

### github actions workflow link

[![.github/workflows/python-ci.yml](https://github.com/agonychaser/devops-s26/actions/workflows/python-ci.yml/badge.svg)](https://github.com/agonychaser/devops-s26/actions/workflows/python-ci.yml)

### docker hub image

images are published to: `https://hub.docker.com/r/razmakhovs/devops-info-service`

tags include:
- `latest` - most recent successful build
- commit sha - exact version reference for reproducibility
- branch name - for tracking per-branch builds

## best practices implemented

### 1. dependency caching

```yaml
- name: Cache Python dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('app_python/requirements.txt') }}
```

**why it helps**: caches pip packages between workflow runs, reducing install time from ~1 minute to ~10 seconds on cache hit. the key is based on `requirements.txt` hash, ensuring cache invalidates when dependencies change.

### 2. job dependencies

```yaml
build-and-push:
  needs: [test, security]
```

**why it helps**: ensures docker images are only built and pushed when tests pass and security scans complete. prevents publishing potentially broken or vulnerable code to docker hub.

### 3. conditional docker push

```yaml
if: github.event_name == 'push'
```

**why it helps**: only pushes images to docker hub on actual pushes (not on pull requests), preventing unnecessary builds and registry bloat.

### 4. built-in pip caching

```yaml
- uses: actions/setup-python@v5
  with:
    cache: 'pip'
```

**why it helps**: leverages github actions' native pip caching for faster dependency installation with minimal configuration.

### 5. ruff linting

```yaml
- name: Run linter (ruff)
  run: |
    cd app_python
    ruff check app.py tests/
```

**why it helps**: fast python linter written in rust. catches code style issues, potential bugs, and import problems before tests run. much faster than alternatives like pylint or flake8.

### 6. snyk security scanning

```yaml
- name: Run Snyk to check for vulnerabilities
  uses: snyk/actions/python@master
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
  with:
    args: --severity-threshold=high
```

**why it helps**: automatically scans dependencies for known vulnerabilities. `--severity-threshold=high` means builds only fail on high/critical issues, allowing medium/low issues to be tracked without blocking development.

### 7. docker build caching

```yaml
- uses: docker/build-push-action@v6
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

**why it helps**: caches docker build layers in github actions cache, significantly reducing build time for subsequent runs.

## key decisions

### versioning strategy: semver

chose semantic versioning because:
- clear communication about api changes (major = breaking, minor = features, patch = fixes)
- industry standard for libraries and services
- allows consumers to pin to specific versions while getting automatic patch updates

### docker tags

ci creates these tags:
- `latest` - always points to most recent successful build
- `{branch-name}` - for tracking branch-specific builds
- `{sha}` - exact commit reference for reproducibility
- `{major}.{minor}` - rolling release branch for minor version
- `{major}.{minor}.{patch}` - exact version (requires git tag)

### workflow triggers

all pushes and pull requests trigger the full workflow:
- push: validates code before/after merging
- pull request: ensures incoming changes pass all checks

this provides fast feedback on all changes while protecting the main branch.

### test coverage

**tested:**
- json structure validation for both endpoints
- required fields presence
- data type verification
- successful responses (200 status)
- error cases (404, 405)
- http method routing

**not tested:**
- external service integration (none exists)
- database operations (not applicable yet)
- complex error scenarios beyond basic 404

## challenges

### challenge: python 3.14 compatibility

**issue**: local development environment uses python 3.14, but pydantic-core (pyo3) doesn't support python 3.14 yet.

**solution**: configured ci to use python 3.12, which is compatible with all dependencies. this demonstrates a key devops principle: ci environment doesn't need to match local dev environment.
