# Lab 03 - Continuous Integration (CI/CD)

## 1. Overview

I used `pytest` for testing because it has clean assertions, strong fixture support, and simple integration with coverage tools. It also fits Flask endpoint testing well through the built-in test client.

The test suite covers:
- `GET /` success response, required JSON structure, and core field validation
- `GET /health` success response and timestamp/uptime checks
- `404` error response for missing endpoints
- `500` error response by forcing an internal exception path

The CI workflows use path filters:
- `python-ci.yml` runs only for `app_python/**` and workflow file changes
- `rust-ci.yml` runs only for `app_rust/**` and workflow file changes

I chose Semantic Versioning for Docker publishing. Tag pushes like `v1.2.3` generate semver tags, while default-branch pushes publish rolling tags (`latest` and `sha-*`).

## 2. Workflow Evidence

Provide links/terminal output for:
- ✅ Successful workflow run: [Python CI workflow](https://github.com/hikariatama/DevOps-Core-Course/actions/workflows/python-ci.yml)
- ✅ Successful workflow run: [Rust CI workflow](https://github.com/hikariatama/DevOps-Core-Course/actions/workflows/rust-ci.yml)
- ✅ Docker image on Docker Hub: [devops-info-service-python](https://hub.docker.com/r/hikariatama/devops-info-service-python)
- ✅ Docker image on Docker Hub: [devops-info-service-rust](https://hub.docker.com/r/hikariatama/devops-info-service-rust)
- ✅ Status badge working in README: see `app_python/README.md`

Local test output:

```bash
$ python3 -m ruff check app.py tests
All checks passed!

$ python3 -m pytest --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=70
collected 4 items
tests/test_app.py ....                                                   [100%]

---------- coverage: platform darwin, python 3.11.9-final-0 ----------
Name     Stmts   Miss  Cover
app.py      58      5    91%
TOTAL       58      5    91%

Required test coverage of 70% reached. Total coverage: 91.38%
```

## 3. Best Practices Implemented

- **Path-based triggers:** avoids wasting CI minutes by running each workflow only when its app changes.
- **Fail-fast quality gate:** Docker publish jobs depend on lint/test jobs, so broken code never gets pushed.
- **Least-privilege permissions:** workflows request only `contents: read` by default.
- **Workflow concurrency:** cancels outdated runs on the same ref to reduce queue time and noise.
- **Matrix testing (Python 3.11 and 3.13):** verifies compatibility across multiple runtime versions.
- **Docker build cache (`type=gha`):** speeds up image rebuilds for unchanged layers.
- **Dependency caching (pip):** configured through `actions/setup-python` cache.
- **Snyk security scan:** integrated with severity threshold `high`, controlled via `SNYK_TOKEN`.

Caching measurement:
- Cold install (empty pip cache): `7.61s`
- Warm install (cache hit): `3.65s`
- Improvement: `3.96s` faster (`~52.0%` reduction)

Snyk note:
- The workflow includes Snyk scanning and will execute when `SNYK_TOKEN` is set in repository secrets.
- Threshold is `high` to fail on high/critical vulnerabilities while reducing low-severity noise.

## 4. Key Decisions

- **Versioning Strategy:** I used SemVer because image consumers can clearly distinguish patch, minor, and major updates from tags. This is more explicit for compatibility expectations than date-based tags.
- **Docker Tags:** The workflows publish semver tags from git release tags (`vX.Y.Z`) and rolling tags (`latest`, `sha-*`). This gives both stable release references and immutable build references.
- **Workflow Triggers:** I used `push` and `pull_request` for `master/main` plus strict path filters. This keeps feedback fast for active changes and avoids running unrelated CI.
- **Test Coverage:** Endpoint behavior, payload structure, and error handlers are tested. Not covered paths are startup logging and direct `app.run(...)` execution block, which are less critical for request-level correctness.

## 5. Challenges (Optional)

- `cargo clippy -D warnings` initially failed on format-string style warnings in Rust source; fixed by switching to inline format args.
- Keeping Docker publish secure required separating quality and publish jobs, then gating publish on successful quality checks.
- Coverage upload and Snyk are secret-dependent, so workflow conditions were added to avoid failing on missing optional tokens.

## Bonus Task - Multi-App CI + Coverage

- Added `.github/workflows/rust-ci.yml` with Rust-specific checks: `cargo fmt --check`, `cargo clippy -D warnings`, and `cargo test`.
- Added path filters to both workflows so Python and Rust pipelines run independently in monorepo changes.
- Added Python coverage generation (`pytest-cov`) and Codecov upload step.
- Added coverage badge and CI status badge to `app_python/README.md`.
