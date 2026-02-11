
# Lab 3: Continuous Integration (CI/CD)

## 1. Overview

### Testing Framework
I chose **pytest** as the testing framework.
**Justification:**
- It requires less boilerplate code compared to `unittest`.
- It has a powerful fixture system (used for the FastAPI `TestClient`).
- It allows running tests with simple commands and integrates well with CI tools.
- **Coverage:** The tests cover the root endpoint (`GET /`), the health check (`GET /health`), and error handling (`404 Not Found`).

### CI/CD Workflow & Docker Strategy

### Workflow Trigger Strategy
The pipeline is defined in `.github/workflows/python-ci.yml` and is configured to trigger on:
*   **Push to `lab3` and `master`:** Ensures immediate feedback during development and continuous integration.
*   **Pull Requests to `master`:** Acts as a quality gate (running tests and linters) before code is merged.
*   **Git Tags (`v*.*.*`):** Triggers production releases (e.g., `v1.0.0`), pushing semantic version tags to Docker Hub.

### Versioning Strategy

I chose **Semantic Versioning (SemVer)**.

Rationale:
This application exposes HTTP endpoints and may evolve over time. 
SemVer clearly communicates whether changes are backward-compatible `(minor/patch) `
or breaking `(major)`, which is important for users pulling Docker images.


### Marketplace Actions Choice
*   **`docker/metadata-action`:** Chosen to automate the complex tagging logic. It dynamically generates tags based on the Git context (branch vs. tag), ensuring we don't need manual scripts.
*   **`docker/setup-buildx-action`:** Essential for enabling **GitHub Actions Cache** export, which drastically speeds up the build process compared to the standard Docker driver.
*   **`snyk/actions/setup`:** Allows installing the Snyk CLI directly to scan local dependencies with specific flags (`--file`), avoiding path issues found in container-based actions.

### Docker Tagging Strategy
I implemented a **hybrid strategy** using `docker/metadata-action`. The tags generated depend on the specific Git event:

1.  **Development (Current State - Branch `lab3`):**
    *   `lab3`: Represents the head of the feature branch.
    *   `sha-<commit-hash>`: Provides a unique, immutable reference for every specific commit (useful for debugging specific builds).
    *   *Evidence:* My current Docker Hub shows `lab3` and `sha-...` tags.

2.  **Production (Future State - After Merge/Tag):**
    *   `latest`: Will be automatically applied when pushing to the default branch (`master`).
    *   `1.2.3` and `1.2`: Will be automatically applied when a Git tag (e.g., `v1.2.3`) is pushed, adhering to **Semantic Versioning (SemVer)**.

---

## 2. Workflow Evidence

###  Successful Workflow Run
- **GitHub Actions:** [Link to Actions Tab](https://github.com/Boogyy/DevOps-Core-Course/actions) 

###  Docker Hub
- **Docker Image:** [Link to DockerHub Repository](https://hub.docker.com/r/egorlazutkin/devops-info-service/tags) 
- **Tags created:** `sha-<commit-hash>`, `lab3` (branch build), `1.0.0` (if tagged).

###  Local Tests Output
Command run: `pytest`
```console
$ pytest
======== test session starts ========
platform darwin -- Python 3.10.7, pytest-8.2.0, pluggy-1.6.0
rootdir: /Users/george/Desktop/Devops/DevOps-Core-Course/app_python
plugins: anyio-4.8.0
collected 4 items                                                                           

tests/test_app.py ....         [100%]

======== 4 passed in 0.40s ========
```

###  Status Badge
The status badge is implemented in the main README.md


---

## 3. Best Practices Implemented

I applied the following CI/CD best practices to ensure a robust pipeline:

1.  **Linter (Flake8):**
    *   **Why:** It runs before testing to catch syntax errors and style issues early. This implements the "Fail Fast" principle.

2.  **Dependency Caching (Pip):**
    *   **Why:** Downloading dependencies takes time. Caching `~/.cache/pip` speeds up the "Install dependencies" step.
    *   **Metric:**
        *   *First Run:* ~45s (downloading all packages).
        *   *Second Run:* ~18s (restoring from cache).
    *   **Improvement:** Saved ~30 seconds per run.
    This demonstrates a noticeable speed improvement due to cache reuse.


3.  **Docker Layer Caching (GitHub Actions Cache):**
    *   **Why:** Rebuilding the entire Docker image is slow. I used `docker/setup-buildx-action` with `cache-from: type=gha` to reuse unchanged layers.
    *   **Result:** Drastically reduced build time for subsequent commits where `requirements.txt` didn't change.

4.  **Security Scanning (Snyk):**
    *   **Why:** Automates the detection of vulnerabilities in open-source dependencies (SCA).
    *   **Implementation:** Added Snyk CLI step to the workflow.
    *   **Findings:** Snyk detected vulnerabilities in `starlette` (via `fastapi`).
    *   **Action Taken:**
        *   Identified issues: `Allocation of Resources Without Limits` and `ReDoS`.
        *   Solution: Updated `fastapi` to version `>=0.115.6` in `requirements.txt` to pull in the patched `starlette` version. (Alternatively, configured `continue-on-error: true` for educational demonstration).

---

## 4. Key Decisions

*   **Versioning Strategy:** **SemVer**. Chosen because this is a service that might have API changes. Consumers need to know if a release is backward-compatible (Minor/Patch) or breaking (Major).
*   **Docker Tags:**
    *   `latest`: For users who always want the newest version.
    *   `branch-name` (e.g., `lab3`): To test specific development branches.
    *   `sha-<commit-hash>`: for debugging specific builds
    *   `x.y.z`: For stable, immutable releases.
*   **Workflow Triggers:** I included `pull_request` to enforce quality gates. Code cannot be merged to `master` unless tests and linter pass.
*   **Test Coverage:** I focused on integration testing of the HTTP endpoints (`/`, `/health`). This provides the most value by verifying the application actually responds to web requests correctly.

## 5. Challenges

*   **Docker Caching:** Initially, the workflow failed with "Cache export is not supported".
    *   *Fix:* Added `docker/setup-buildx-action` to enable the extended build capabilities required for GitHub Actions caching.
*   **Snyk Integration:** The `snyk/actions/python` container couldn't find the requirements file in the subdirectory.
    *   *Fix:* Switched to installing Snyk CLI (`snyk/actions/setup`) and running `snyk test --file=app_python/requirements.txt` explicitly.
