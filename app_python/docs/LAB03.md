# LAB03 — Continuous Integration (CI/CD)

## 1. Overview

**Testing Framework:** pytest  
**Why:** Simple syntax, FastAPI TestClient works out of the box, minimal boilerplate, industry standard

**Tested endpoints:**
- `GET /` — status 200, JSON structure (service, system, runtime, request, endpoints), required fields (name, version)
- `GET /health` — status 200, fields: status="healthy", timestamp, uptime_seconds
- Error cases — 404 Not Found, 405 Method Not Allowed

**CI Workflow Triggers:**
- `push` to `main`, `master`, `lab*` branches
- `pull_request` to `main`/`master`
- No path filters (basic implementation)

**Versioning Strategy:** Calendar Versioning (CalVer)  
**Format:** `YYYY.MM.DD-RUN_NUMBER` (example: `2026.02.13-42`)  
**Why:** This is a web service with continuous deployment — build date gives more context than semantic versioning. Users need to know *when* it was built, not what breaking changes were introduced.

---

## 2. Workflow Evidence

### Successful workflow run

https://github.com/Amirhan-322/DevOps-Core-Course/actions/runs/21957444272

Also you can see done workflow in the screenshot `08-workflow-jobs-done.png`


### Tests passing locally

You can see the pytest output in the screenshot `09-pytest-output.png`

### Docker Hub images

- Repository: https://hub.docker.com/r/YOUR_USERNAME/devops-info-service
- Tags: latest, 2026.02.13-42, 2026.02

Screenshot: `10-docker-hub-workflow-generated-repo`

---

## 3. Best Practices Implemented

| Practice | Implementation | Why & Result |
|----------|---------------|--------------|
| **Dependency Caching** | `actions/setup-python` with `cache: pip` and `cache-dependency-path` | Pip packages are reused between runs. |
| **Fail Fast** | `needs: test-and-lint` in jobs | Docker image is only built and pushed if all tests pass. No wasted resources on broken code. |
| **Conditional Docker Push** | `if: github.event_name == 'push'` | Images are only pushed on direct pushes, not on every PR commit. Keeps tag history clean. |
| **Docker Layer Caching** | `cache-from: type=gha` and `cache-to: type=gha,mode=max` | Docker layers are reused across workflow runs. |
| **Status Badge** | Added to `app_python/README.md` | Provides immediate visual feedback on build status directly in repository homepage. |

**Note on Security Scanning:**  
Snyk integration was not implemented due to accessibility limitations. All dependencies are up to date with current versions.

---

## 4. Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Versioning Strategy** | Calendar Versioning (CalVer) | This is a continuously deployed web service, not a library. Date-based versions (2026.02.13-42) tell operators exactly when the image was built. SemVer would require manual tagging and doesn't add value here. |
| **Docker Tags** | `latest`, `YYYY.MM.DD-RUN`, `YYYY.MM` | `latest` for convenience and default pulls. Full version tag for exact rollback. Monthly tag for environment pinning. Every build gets a unique, traceable tag. |
| **Workflow Triggers** | Push to branches | Push triggers give immediate feedback during development. |
| **Test Coverage** | 7 tests covering all endpoints | Tested: status codes (200, 404, 405), JSON structure, required fields, error responses. Not tested: environment configuration. |

---

## 5. Challenges & Solutions

| Challenge | Solution |
|----------|----------|
| **Workflow not triggering** | workflow now runs on push |
| **Docker push authentication failed** | Added `docker/login-action@v3` before build step and stored Docker Hub token in GitHub Secrets |
| **Cache was not restoring** | Added `cache-dependency-path: app_python/requirements*.txt` to point actions/setup-python to correct location |
| **Tests passed locally but failed in CI** | Fixed relative imports with `sys.path.insert(0, ...)` in test file |
| **Snyk unavailable** | Skipped security scanning task, documented limitation |