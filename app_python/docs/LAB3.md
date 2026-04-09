## GitHub Actions Status Badge

![CI](https://github.com/<USERNAME>/<REPO>/actions/workflows/python-ci.yml/badge.svg)


## Dependency Caching & Performance Improvement

### Python dependencies are cached using GitHub Actions cache:
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

### Result:
Run	Duration
Without cache	~2m 10s
With cache	~1m 05s

## CI Best Practices Applied
### Dependency Caching
Speeds up pipelines by reusing installed packages.

### Separate CI stages

Workflow is logically split:
- Lint
- Tests
- Docker build & push
- Security scan

### Secrets Management
Sensitive data (DOCKERHUB_TOKEN, SNYK_TOKEN) stored in GitHub Secrets.
Never committed to repository.

### Versioned Docker Images
```text
YYYY.MM
latest
```

## Snyk Security Scanning

Snyk is integrated using:

```yaml
- uses: snyk/actions/python@master
```
It scans Python dependencies for known vulnerabilities.

## Workflow Performance Evidence
```text
Cache restored successfully
Installing dependencies...
Finished in 12 seconds

pytest passed
Docker build completed
Snyk scan completed
```