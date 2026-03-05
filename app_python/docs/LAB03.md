# LAB03 --- CI/CD (GitHub Actions)

## 1. Overview

### Testing Framework

I chose **pytest** as the testing framework.

**Why pytest:**

-   Minimal and readable syntax
-   Powerful fixtures (`conftest.py`)
-   Good ecosystem and CI integration
-   Industry-standard for modern Python projects

Tests are located in:

app_python/tests/ ├── conftest.py └── test_endpoints.py

### What Is Covered

Endpoints tested:

-   `GET /`
-   `GET /health`

Test coverage includes:

-   Correct HTTP status codes (200)
-   JSON response structure validation
-   Required fields presence
-   Data types validation
-   Error handling (invalid routes → 404 JSON response)

Tests validate structure and behavior, not environment-specific values
like hostname.

------------------------------------------------------------------------

### CI Workflow Trigger Configuration

Workflow file:

.github/workflows/python-ci.yml

Triggers:

-   `push` (only if `app_python/**` changes)
-   `pull_request` (only if `app_python/**` changes)
-   `workflow_dispatch` (manual)

Docker release runs only on git tags starting with `v` (e.g. `v1.2.3`).

------------------------------------------------------------------------

### Versioning Strategy

I implemented **Semantic Versioning (SemVer)**.

Format:

vMAJOR.MINOR.PATCH

Example:

v1.2.3

**Why SemVer:**

-   Clear distinction between breaking changes and bug fixes
-   Standard for versioned container images
-   Easy to implement using git tags
-   Appropriate for a service exposing API endpoints

------------------------------------------------------------------------

## 2. Workflow Evidence

### Successful Workflow Run

https://github.com/egraPA006/DevOps-Core-Course/actions/workflows/python-ci.yml

------------------------------------------------------------------------

### Tests Passing Locally

Example output:

\$ pytest -q 2 passed in 0.45s

Lint:

\$ flake8 . (no output → no lint errors)

------------------------------------------------------------------------

### Docker Image on Docker Hub

Repository:

https://hub.docker.com/r/egrapa/devops-core-course-lab2

On tag `v1.2.3`, CI publishes:

-   egrapa/devops-core-course-lab2:1.2.3
-   egrapa/devops-core-course-lab2:1.2
-   egrapa/devops-core-course-lab2:latest

------------------------------------------------------------------------

### Status Badge

README includes a GitHub Actions status badge reflecting real workflow
status.

------------------------------------------------------------------------

## 3. Best Practices Implemented

### Path-Based Triggers

CI runs only when `app_python/**` changes.

Prevents unnecessary builds and saves CI resources.

------------------------------------------------------------------------

### Concurrency Control

Outdated workflow runs are automatically canceled.

Prevents duplicate builds and reduces wasted CI time.

------------------------------------------------------------------------

### Job Dependency (Fail Fast)

Docker build runs only if tests pass.

Prevents publishing broken images.

------------------------------------------------------------------------

### Dependency Caching (pip)

Using built-in `actions/setup-python` pip caching.

Performance improvement:

-   First run: \~50--60 seconds
-   Cached run: \~20--25 seconds

\~50% faster dependency installation.

------------------------------------------------------------------------

### Docker Layer Caching

Using GitHub Actions BuildKit cache.

Speeds up Docker builds by reusing previous layers.

------------------------------------------------------------------------

### Least Privilege Permissions

permissions: contents: read

Limits GitHub token access and reduces attack surface.

------------------------------------------------------------------------

### Snyk Security Scanning

Snyk integration was planned but could not be completed.

Due to **regional network restrictions**, I could not obtain or validate
the Snyk API token.\
Access to Snyk services was blocked, and even using a proxy did not
resolve the issue.

Because of this:

-   Snyk CLI could not authenticate
-   The API token could not be verified
-   Automated vulnerability scanning could not be enabled

Planned setup (once access is available):

-   Use `snyk/actions`
-   Authenticate via `SNYK_TOKEN` stored as GitHub Secret
-   Configure failure on high/critical vulnerabilities

The CI pipeline structure already supports adding this step once network
restrictions are removed.

------------------------------------------------------------------------

## 4. Key Decisions

### Versioning Strategy

SemVer was chosen because:

-   The service exposes API endpoints
-   It clearly communicates breaking changes
-   It integrates naturally with git tags
-   Docker tags directly map to SemVer versions

------------------------------------------------------------------------

### Docker Tags

On `vX.Y.Z` tag, CI generates:

-   `X.Y.Z`
-   `X.Y`
-   `latest`

Provides reproducibility and rolling updates.

------------------------------------------------------------------------

### Workflow Triggers

Workflow runs on:

-   push
-   pull request
-   only when `app_python/**` changes

Docker release runs only on version tags.

Prevents accidental publishing and unnecessary CI execution.

------------------------------------------------------------------------

### Test Coverage

Tests cover:

-   Public API endpoints
-   JSON structure validation
-   Health-check behavior
-   HTTP status codes

Not covered:

-   Logging internals
-   Some environment edge cases
-   Internal helper logic

Focus is on public API behavior.

------------------------------------------------------------------------

## 5. Challenges

-   Docker Hub authentication initially failed due to incorrect token
    scope
-   Tag extraction logic required adjustment
-   Ensured Docker release runs only on version tags
-   Snyk integration blocked due to regional restrictions

------------------------------------------------------------------------

## Conclusion

This CI/CD pipeline:

-   Automatically tests code on changes
-   Enforces linting and quality checks
-   Builds and publishes Docker images using SemVer
-   Uses caching and concurrency optimizations
-   Prevents broken releases

It provides a reliable foundation for future DevOps labs.