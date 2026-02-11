# Lab 3 — Continuous Integration (CI/CD)

## 1. Overview

### Testing Framework — pytest

**Choice:** pytest 8.3  
**Why:**
- Simple, concise assertion syntax (plain `assert`)
- Powerful fixture system for test setup/teardown
- Excellent plugin ecosystem (pytest-cov for coverage)
- De-facto standard for modern Python projects

| Framework | Syntax | Fixtures | Plugins | Built-in |
|-----------|--------|----------|---------|----------|
| **pytest** | Simple `assert` | Yes | Rich ecosystem | No (pip) |
| unittest | `self.assertEqual()` | setUp/tearDown | Limited | Yes |
| nose2 | `assert` | Yes | Moderate | No |

### Test Coverage

Tests cover **all** endpoints and error handling:

| Area | Tests |
|------|-------|
| `GET /` | Status code, JSON structure, all 5 sections, field types |
| `GET /health` | Status code, fields, uptime, timestamp format |
| `404 handling` | Unknown routes return 404 JSON with path |
| Helper functions | `get_uptime()`, `get_system_info()`, `START_TIME` |

### CI Workflow Triggers

The workflow runs on:
- **Push** to `master`, `main`, `lab03` branches (only when `app_python/` or the workflow file changes)
- **Pull requests** to `master`/`main` (same path filter)

### Versioning Strategy — SemVer

**Choice:** Semantic Versioning (v1.0.0)  
**Rationale:** The DevOps Info Service is an API — consumers need to know when breaking changes occur. SemVer communicates this through the version number itself (MAJOR = breaking, MINOR = feature, PATCH = fix). For a service that will evolve through the course, SemVer provides a clear upgrade path.

Docker images are tagged with:
- `latest` (on default branch push)
- `1.0.0` (semantic version)
- Short commit SHA (for traceability)

---

## 2. Workflow Evidence

- **Successful workflow run:** `https://github.com/Ravwvil/DevOps-Core-Course/actions/workflows/python-ci.yml`
- **Tests passing locally:** *(add terminal output screenshot when running locally)*
- **Docker Hub image:** `https://hub.docker.com/r/ravwvil/devops-info-service`
- **Coveralls dashboard:** `https://coveralls.io/github/Ravwvil/DevOps-Core-Course`
- **Status badge:** Visible at the top of `app_python/README.md`

---

## 3. Best Practices Implemented

| Practice | Why It Helps |
|----------|-------------|
| **Dependency caching** | `actions/setup-python` caches pip packages keyed by `requirements.txt` hash — avoids re-downloading on every run, saving ~30-60s |
| **Snyk security scan** | Checks dependencies against known CVE databases; catches supply-chain vulnerabilities before they reach production |
| **Status badge** | Immediate visual feedback on repo health; anyone can see if CI is passing without opening the Actions tab |
| **Workflow concurrency** | `cancel-in-progress: true` stops outdated runs when you push again, saving runner minutes |
| **Job dependencies** | Docker build (`docker` job) only runs if `test` job passes — never pushes a broken image |
| **Path-based triggers** | Workflow only fires on `app_python/` changes — Go-only commits don't waste Python CI time |
| **Fail fast** | Tests use `--cov-fail-under=70` — PR is blocked if coverage drops below threshold |

### Caching Details

- **Cache key:** `hashFiles('app_python/requirements.txt')`
- **Expected improvement:** ~30-60 seconds saved per run (dependency install reduced from ~40s to ~5s on cache hit)

### Coverage Integration

- **Service:** Coveralls.io (free for public repos)
- **Report format:** Cobertura XML (from pytest-cov)
- **Base path:** `app_python/` (for monorepo support)
- **Current coverage:** 87% on app.py (95% total including tests)
- **Coverage threshold:** 70% minimum (`--cov-fail-under=70` in pytest)

### Snyk Results

- Severity threshold set to **high** (low/medium findings don't block the build)
- `continue-on-error: true` to avoid hard-blocking on informational findings
- Any critical/high vulnerabilities should be addressed by upgrading the affected package

---

## 4. Key Decisions

### Versioning Strategy
**SemVer** — the service exposes a JSON API that other tools/labs depend on. Semantic versioning makes it clear whether an update is safe to pull (`PATCH`) or requires consumer changes (`MAJOR`). CalVer was considered but doesn't communicate API compatibility.

### Docker Tags
Each CI push produces up to 3 tags:
1. `latest` — always points to the newest build on the default branch
2. `1.0.0` — pinned version for reproducibility
3. `<sha>` — short commit hash for exact traceability

### Workflow Triggers
- Push triggers on `master`/`main`/`lab03` ensure CI runs during development
- PR triggers act as a gate — code can't be merged if CI fails
- Path filters prevent unnecessary runs when unrelated files change

### Test Coverage
- All HTTP endpoints are tested (status codes, JSON structure, field types)
- Helper functions are tested independently
- Error handling (404) is tested
- **Not tested:** `__main__` block (server startup) — this is runtime entry code, not business logic

---

## 5. Challenges

- **FastAPI test client:** Requires `httpx` as a dependency — added to `requirements.txt`
- **Path filters vs. first run:** On the very first push of a workflow file, GitHub may not trigger it if the path filter doesn't match. Fixed by including the workflow file path itself in the `paths` list
- **Snyk token setup:** Requires manual configuration in GitHub Secrets (see instructions below)
