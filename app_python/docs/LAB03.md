# Lab 03 — CI/CD

## Overview

- **Testing framework:** pytest — simple syntax, powerful fixtures, works great with FastAPI's `TestClient`. No reason to use verbose `unittest` for a project this size.
- **Tests cover:** `GET /` (8 tests), `GET /health` (6 tests), error handling (2 tests) — 16 tests total.
- **CI triggers:** push to `master`/`lab03` and PRs to `master`, only when `app_python/**` files change.
- **Versioning:** CalVer (`YYYY.MM.RUN_NUMBER`) — this is a service, not a library. Date-based tags make it obvious when an image was built.

## Workflow Evidence

- Successful workflow run: https://github.com/4hellboy4/DevOps-Core-Course/actions/runs/21961258045
- Tests passing locally: see `screenshots/13-running-tests.png`
- Docker Hub: https://hub.docker.com/r/4hellboy4/devops-info-service
- Status badge is at the top of `app_python/README.md`

## Best Practices Implemented

- **Dependency caching:** `actions/setup-python` caches pip packages keyed on `requirements-dev.txt` hash. First run downloads everything, subsequent runs skip installation. Saves ~15-20 seconds per run.
- **Job dependencies:** Docker build (`needs: test`) only runs if lint + tests pass. No point pushing a broken image.
- **Path filters:** Workflow only triggers on `app_python/**` changes. Editing Go code or docs doesn't waste CI minutes.
- **Concurrency control:** `cancel-in-progress: true` kills outdated runs when you push again quickly. No zombie workflows.
- **Conditional Docker push:** `if: github.event_name == 'push'` — PRs run tests only, don't push to Docker Hub.
- **Snyk scanning:** Runs after tests with `continue-on-error: true` and `--severity-threshold=high`. Warns about vulnerable dependencies without blocking the build for low-severity issues.

## Key Decisions

- **CalVer over SemVer:** This service doesn't have "breaking changes" — it's an info endpoint. CalVer (`2026.02.5`) tells you exactly when it was built. SemVer would be overkill.
- **Docker tags:** Each push creates `YYYY.MM.RUN_NUMBER` + `latest`. Two tags so you can pin a specific version or always get the newest.
- **Triggers:** Push + PR on `app_python/**` only. PRs run tests (catch bugs before merge), pushes also build and push Docker images.
- **Test coverage:** All three endpoints tested — `/` checks every JSON field and type, `/health` checks status and uptime, 404 checks the custom error handler. Not testing internal service functions directly because the endpoint tests already exercise them.

## Challenges

- Had to add `sys.path.insert` in test files because pytest runs from the repo root but the app modules are inside `app_python/`.
- Snyk needs a separate API token — created a free account and added `SNYK_TOKEN` to GitHub Secrets.

---

## Bonus: Multi-App CI + Coverage

### Go CI Workflow

Created `.github/workflows/go-ci.yml` with the same structure as the Python workflow:
- **Lint:** `golangci-lint` (standard Go linter)
- **Test:** `go test -v ./...`
- **Docker:** Multi-stage build, same CalVer tagging, pushes to `4hellboy4/devops-info-service-go`

Path filters ensure Go CI only runs on `app_go/**` changes. Both workflows run in parallel when both apps change in one commit.

### Path Filters

Each workflow only triggers on its own app directory:
- `python-ci.yml` → `app_python/**`
- `go-ci.yml` → `app_go/**`

This avoids wasting CI minutes. If you edit only Go code, the Python workflow doesn't run, and vice versa.

### Coverage

- Integrated `pytest-cov` into the Python CI — runs `pytest --cov=. --cov-report=xml`
- Coverage reports uploaded to Codecov via `codecov/codecov-action@v4`
- Coverage badge added to `app_python/README.md`
- Testing all endpoints through the TestClient gives good coverage of routes, services, and models. Config and `__main__` block are intentionally untested (startup code, not logic).
