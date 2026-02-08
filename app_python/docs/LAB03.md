# LAB03 — Continuous Integration (CI/CD)

## 1. Overview

The Python application was implemented in previous labs and reused without modification.
In this lab, automated testing, CI/CD, and security scanning were added.

**Testing framework:** pytest  
Chosen for its simple syntax, rich ecosystem, and excellent CI integration.

**Test coverage:**
- GET / — verifies JSON structure and required fields
- GET /health — verifies service health response
- Error case — non-existing endpoint

**CI triggers:**
- push to lab03, master, main
- pull_request
- path filters to avoid running CI on unrelated changes

**Versioning strategy:** Calendar Versioning (CalVer)  
Format: YYYY.MM.DD + latest  
Chosen because releases are time-based and frequent.

---

## 2. Workflow Evidence

- GitHub Actions run: <ADD LINK TO SUCCESSFUL RUN>
- Local test output:
2 passed in 3.94s

- Docker Hub image: <ADD DOCKER HUB LINK>
- CI status badge: added to README

---

## 3. CI Best Practices Implemented

- Dependency caching using `actions/setup-python` (pip cache).
- Docker layer caching using GitHub Actions cache.
- Job dependency: Docker build runs only if tests pass.
- Path-based workflow triggers to reduce unnecessary CI runs.
- Security scanning with Snyk.

**Caching impact:**  
Subsequent CI runs are faster due to dependency and Docker layer caching (observed in Actions logs).

---

## 4. Security Scanning (Snyk)

Snyk was integrated into the CI pipeline to scan Python dependencies for known vulnerabilities.

**Result:**  
No critical vulnerabilities were found (or vulnerabilities were reviewed and accepted for lab purposes).

---

## 5. Key Decisions

- pytest was selected for its simplicity and CI friendliness.
- CalVer was chosen instead of SemVer for time-based lab releases.
- Docker images are tagged with `latest` and date-based version.
- Path filters were used to optimize CI execution in a multi-folder repository.

---

## 6. Challenges

- Handling macOS PEP 668 restrictions required using virtual environments.
- Aligning local, CI, and Docker configurations required consistent port usage.
