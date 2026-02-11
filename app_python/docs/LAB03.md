# LAB03 — Continuous Integration (CI/CD)

## 1. Overview
- **Testing framework:** `unittest` (Python standard library)
- **Why unittest:** no extra package required, deterministic behavior, and straightforward route-level endpoint testing via in-memory ASGI requests.
- **Tested endpoints/functionality:** `GET /`, `GET /health`, plus error behavior (`GET /does-not-exist` -> `404`, `POST /health` -> `405`).
- **CI workflow triggers:** On `push` to `master`, `main`, or `lab03`; on `pull_request` to `master`/`main`; and manual `workflow_dispatch`. The workflow runs only when `app_python/**` or `.github/workflows/python-ci.yml` changes.
- **Versioning strategy:** **CalVer** using UTC date tags generated in CI.

## 2. Workflow Evidence
Provide links/terminal output for:
- ✅ Successful workflow run (GitHub Actions link): Pending Task 2.
- ✅ Tests passing locally (terminal output):

```bash
python3 -m unittest -v
test_health_rejects_post_method (tests.test_app.TestAppEndpoints.test_health_rejects_post_method) ... ok
test_health_returns_expected_payload (tests.test_app.TestAppEndpoints.test_health_returns_expected_payload) ... ok
test_root_falls_back_to_client_ip_without_forwarded_header (tests.test_app.TestAppEndpoints.test_root_falls_back_to_client_ip_without_forwarded_header) ... ok
test_root_returns_expected_structure (tests.test_app.TestAppEndpoints.test_root_returns_expected_structure) ... ok
test_root_uses_forwarded_for_header (tests.test_app.TestAppEndpoints.test_root_uses_forwarded_for_header) ... ok
test_unknown_endpoint_returns_404 (tests.test_app.TestAppEndpoints.test_unknown_endpoint_returns_404) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.008s

OK
```

- ✅ Docker image on Docker Hub (link to your image): `https://hub.docker.com/r/ebortsov/devops-info/tags`
- ✅ Status badge working in README: Pending Task 3.

## 3. Best Practices Implemented
- **Practice 1:** Endpoint-level tests validate actual HTTP behavior (status codes and payloads), not only internal function calls.
- **Practice 2:** Included error-path tests (`404`, `405`) to catch regressions in routing and method handling.
- **Practice 3:** Separated dev dependencies into `requirements-dev.txt` to keep runtime image minimal and reproducible.
- **Actions selection:** Used official maintained actions (`actions/checkout`, `actions/setup-python`, `docker/login-action`, `docker/build-push-action`) for predictable behavior and security support.
- **Caching:** Pending Task 3.
- **Snyk:** Pending Task 3.

## 4. Key Decisions
- **Versioning Strategy:** **CalVer** (`YYYY.MM.DD`) was chosen because this app behaves like a continuously updated service where release date is a clear and practical version marker.
- **Docker Tags:** CI creates three tags per push: `YYYY.MM.DD`, `YYYY.MM`, and `latest`. This provides both precise and rolling references.
- **Workflow Triggers:** Push and PR triggers enforce quality checks automatically, while the Docker push job runs only on push events after tests pass.
- **Test Coverage:** Current tests cover both public endpoints and common HTTP error paths; deeper coverage metrics will be added in the bonus coverage task.

## 5. Challenges (Optional)
- Initial tests used direct async function calls and did not validate HTTP status behavior.
- Updated tests to ASGI request/response testing so route-level behavior is validated without extra dependencies.
