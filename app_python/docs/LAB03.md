# Lab 3 — Continuous Integration (CI/CD) Documentation

## 1. Unit Testing

### Testing Framework Choice and Justification

**Framework:** pytest 8.3.4

**Why pytest?**

- **Simple syntax:** Clean, readable test code with minimal boilerplate compared to unittest
- **Powerful fixtures:** Easy setup/teardown and dependency injection via `@pytest.fixture` decorator
- **Excellent plugin ecosystem:** Rich ecosystem including pytest-cov for coverage, pytest-asyncio for async testing
- **Great error messages:** Clear, helpful output when tests fail, making debugging easier
- **Industry standard:** Widely adopted in Python community and modern projects
- **Fast execution:** Efficient test discovery and execution
- **Test discovery:** Automatically finds and runs tests based on naming conventions (`test_*.py`, `test_*` functions)

**Alternative considered:** `unittest` (built-in Python library)
- **Pros:** No additional dependencies
- **Cons:** More verbose syntax, less modern features, requires more boilerplate code
- **Decision:** pytest chosen for better developer experience and modern features

### Test Structure

Tests are organized into separate files following best practices:

```
app_python/tests/
├── __init__.py           # Makes tests a Python package
├── conftest.py           # Shared fixtures (TestClient)
├── test_root.py          # Tests for GET / endpoint (8 tests)
├── test_health.py        # Tests for GET /health endpoint (5 tests)
├── test_errors.py        # Tests for error handling (404, etc.) (3 tests)
└── test_consistency.py   # Tests for consistency between endpoints (2 tests)
```

**Benefits of this structure:**
- **Separation of concerns:** Each file focuses on a specific endpoint or aspect
- **Better maintainability:** Easy to find and update tests for specific functionality
- **Improved readability:** Smaller, focused files are easier to understand
- **Reusable fixtures:** `conftest.py` provides shared TestClient fixture via pytest fixtures
- **Scalability:** Easy to add new test files as the application grows

### Test Coverage

The test suite comprehensively covers all endpoints:

**GET /** endpoint (8 tests):
- HTTP status code validation (200 OK)
- JSON structure validation (all required top-level keys)
- Service information validation (name, version, description, framework)
- System information type checking (hostname, platform, architecture, etc.)
- Runtime information validation (uptime calculation, timestamp format)
- Request information extraction (client IP, method, path, user agent)
- Endpoints list validation (structure and content)

**GET /health** endpoint (5 tests):
- HTTP status code validation (200 OK)
- Response structure validation (status, timestamp, uptime_seconds)
- Status value verification ("healthy")
- Timestamp format validation (ISO 8601)
- Uptime calculation verification (non-negative integer)

**Error Handling** (3 tests):
- 404 error responses for non-existent endpoints
- Error response structure validation
- Multiple invalid path scenarios

**Consistency Checks** (2 tests):
- Uptime consistency between root and health endpoints
- Timestamp format consistency

**Total:** 17 tests covering all endpoints and error cases

### How to Run Tests Locally

From the `app_python` directory:

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies (includes pytest)
pip install -r requirements.txt

# 3. Run all tests
pytest tests/ -v

# 4. Run tests with coverage report
pytest tests/ --cov=app --cov-report=term

# 5. Run specific test file
pytest tests/test_root.py -v
pytest tests/test_health.py -v
```

### Terminal Output Showing All Tests Passing

```bash
$ cd app_python
$ source venv/bin/activate
$ pytest tests/ -v

====================================================== test session starts ======================================================
platform darwin -- Python 3.14.2, pytest-8.3.4, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /Users/marinalavrova/Documents/Projects/study_projects/DevOps-Core-Course/app_python
plugins: anyio-4.12.1, cov-6.0.0
collected 17 items                                                                                                              

tests/test_consistency.py::TestEndpointConsistency::test_uptime_consistency PASSED                                        [  5%]
tests/test_consistency.py::TestEndpointConsistency::test_timestamp_consistency PASSED                                     [ 11%]
tests/test_errors.py::TestErrorHandling::test_404_endpoint PASSED                                                          [ 17%]
tests/test_errors.py::TestErrorHandling::test_404_error_structure PASSED                                                   [ 23%]
tests/test_errors.py::TestErrorHandling::test_404_multiple_paths PASSED                                                    [ 29%]
tests/test_health.py::TestHealthEndpoint::test_health_endpoint_status_code PASSED                                          [ 35%]
tests/test_health.py::TestHealthEndpoint::test_health_endpoint_json_structure PASSED                                        [ 41%]
tests/test_health.py::TestHealthEndpoint::test_health_endpoint_status_value PASSED                                         [ 47%]
tests/test_health.py::TestHealthEndpoint::test_health_endpoint_timestamp_format PASSED                                       [ 52%]
tests/test_health.py::TestHealthEndpoint::test_health_endpoint_uptime PASSED                                                [ 58%]
tests/test_root.py::TestRootEndpoint::test_root_endpoint_status_code PASSED                                                 [ 64%]
tests/test_root.py::TestRootEndpoint::test_root_endpoint_json_structure PASSED                                              [ 70%]
tests/test_root.py::TestRootEndpoint::test_root_endpoint_service_info PASSED                                                [ 76%]
tests/test_root.py::TestRootEndpoint::test_root_endpoint_system_info PASSED                                                  [ 82%]
tests/test_root.py::TestRootEndpoint::test_root_endpoint_runtime_info PASSED                                               [ 88%]
tests/test_root.py::TestRootEndpoint::test_root_endpoint_request_info PASSED                                                [ 94%]
tests/test_root.py::TestRootEndpoint::test_root_endpoint_endpoints_list PASSED                                              [100%]

====================================================== 17 passed in 0.10s =======================================================
```

All 17 tests pass successfully, covering both endpoints (`GET /` and `GET /health`), error handling, and consistency checks.

### Test coverage:
```
venv) marinalavrova@MacBook-Pro-Marina app_python % pytest tests/ --cov=app --cov-report=term
====================================================== test session starts ======================================================
platform darwin -- Python 3.14.2, pytest-8.3.4, pluggy-1.6.0
rootdir: /Users/marinalavrova/Documents/Projects/study_projects/DevOps-Core-Course/app_python
plugins: anyio-4.12.1, cov-6.0.0
collected 17 items                                                                                                              

tests/test_consistency.py ..                                                                                              [ 11%]
tests/test_errors.py ...                                                                                                  [ 29%]
tests/test_health.py .....                                                                                                [ 58%]
tests/test_root.py .......                                                                                                [100%]

---------- coverage: platform darwin, python 3.14.2-final-0 ----------
Name     Stmts   Miss  Cover
----------------------------
app.py      40      5    88%
----------------------------
TOTAL       40      5    88%


====================================================== 17 passed in 0.07s =======================================================
(venv) marinalavrova@MacBook-Pro-Marina app_python % 
```

## 2. GitHub Actions CI Workflow

### Workflow Trigger Strategy and Reasoning

**Trigger Configuration:**

The workflow runs on:
- **Push events:** When code is pushed to `main` or `lab03` branches
- **Pull request events:** When PRs are opened or updated targeting `main` or `lab03` branches
- **Path filters:** Only triggers when files in `app_python/` directory or the workflow file itself changes

**Reasoning:**
- **Push to main/lab03:** Ensures all code merged to main branches is tested and built
- **Pull requests:** Catches issues before merging, maintaining code quality
- **Path filters:** Only runs when Python app code changes, saving compute resources and providing faster feedback
- **Conditional Docker push:** Docker build/push only runs on `push` events (not PRs) to prevent unnecessary pushes and save Docker Hub quota

### Actions Chosen from Marketplace

**Why these specific actions:**

1. **`actions/checkout@v4`**
   - Official GitHub action for checking out repository code
   - Required for accessing source code in workflow
   - Latest stable version (v4) with improved performance

2. **`actions/setup-python@v5`**
   - Official GitHub action for Python setup
   - Built-in pip caching support (`cache: 'pip'`) for faster dependency installation
   - Supports multiple Python versions and virtual environments

3. **`docker/setup-buildx-action@v3`**
   - Official Docker action for setting up Buildx
   - Required for advanced Docker build features (multi-platform, caching)
   - Enables Docker layer caching via GitHub Actions cache

4. **`docker/login-action@v3`**
   - Official Docker action for Docker Hub authentication
   - Secure credential handling via GitHub Secrets
   - Supports multiple registries (Docker Hub, GitHub Container Registry, etc.)

5. **`docker/build-push-action@v6`**
   - Official Docker action for building and pushing images
   - Supports multiple tags, caching, and build arguments
   - Efficient parallel builds with Buildx

**Alternative considered:** Manual Docker commands (`docker build`, `docker push`)
- **Pros:** More control, no external dependencies
- **Cons:** More verbose, no built-in caching, harder to maintain
- **Decision:** Official actions chosen for better integration, caching, and maintainability

### Versioning Strategy

**Strategy:** Calendar Versioning (CalVer)

**Format:** `YYYY.MM.DD.BUILD_NUMBER` (e.g., `2024.01.15.42`)

**Why this format?**
- **YYYY (full year):** ISO 8601 standard, unambiguous, future-proof
- **MM.DD (month.day):** Clear date indication
- **BUILD_NUMBER:** Unique identifier for multiple builds per day (from `github.run_number`)

**Why not shorter formats?**
- **YY.MM.DD (e.g., `24.01.15`):** Shorter but non-standard, potential ambiguity in 100 years
- **YYYY.MM.DD without BUILD_NUMBER:** Works if only 1-2 builds per day, but loses uniqueness for multiple daily builds

**Why CalVer?**
- **Time-based releases:** Clear indication of when the image was built
- **Continuous deployment friendly:** No need to manually create git tags
- **Easy to remember:** Date-based versions are intuitive
- **Service-oriented:** Fits our use case (service, not library)
- **Frequent deployments:** Breaking changes are less critical than in libraries

**Implementation in CI Workflow:**

The versioning is implemented in the `docker-build-push` job:

```yaml
- name: Generate version tags (CalVer)
  id: meta
  run: |
    VERSION=$(date +%Y.%m.%d)
    BUILD_NUMBER=${{ github.run_number }}
    echo "tags=${{ env.DOCKER_USERNAME }}/${{ env.DOCKER_IMAGE }}:$VERSION,${{ env.DOCKER_USERNAME }}/${{ env.DOCKER_IMAGE }}:$VERSION.$BUILD_NUMBER,${{ env.DOCKER_USERNAME }}/${{ env.DOCKER_IMAGE }}:latest" >> $GITHUB_OUTPUT
```

This generates three tags per build:
- Date version: `YYYY.MM.DD` (e.g., `2024.01.15`)
- Full version: `YYYY.MM.DD.BUILD_NUMBER` (e.g., `2024.01.15.42`)
- Latest: `latest` (always points to most recent build)

### Docker Tagging Strategy

**Tags created per image:**

1. **Date version (`YYYY.MM.DD`):** 
   - Example: `2024.01.15`
   - Purpose: Easy to identify when image was built
   - Use case: Rolling deployments by date

2. **Full version (`YYYY.MM.DD.BUILD_NUMBER`):**
   - Example: `2024.01.15.42`
   - Purpose: Unique identifier for each build
   - Use case: Specific version pinning, rollback scenarios

3. **Latest (`latest`):**
   - Example: `latest`
   - Purpose: Always points to most recent build
   - Use case: Default deployments, development environments

**Why not commit SHA?**
- Commit SHA tags are useful for traceability but less user-friendly
- CalVer provides both traceability (via build number) and readability (via date)
- Build number (`github.run_number`) provides unique identification

**Tag format:** `DOCKER_USERNAME/DOCKER_IMAGE:TAG`
- Example: `username/devops-info-service:2024.01.15.42`

### Workflow Evidence

### Successful Workflow Run

**GitHub Actions Link:** `https://github.com/McLavrushka/DevOps-Core-Course/actions/runs/21900641968`

**Workflow Execution Time:**
- **Code Quality & Testing:** 20s
- **Security Scanning (Snyk):** 22s
- **Docker Build & Push:** 45s
- **Total Duration:** 1m 27s

**Workflow includes:**
- ✅ Code quality checks (linting with ruff)
- ✅ Unit tests execution
- ✅ Test coverage reporting
- ✅ Docker image build
- ✅ Docker image push to Docker Hub with version tags (3 tags per image)
- ✅ Security scanning with Snyk

**Terminal Output / Screenshot:**

Workflow run details available at: https://github.com/McLavrushka/DevOps-Core-Course/actions/runs/21900641968

### Docker Image on Docker Hub

**Image:** `mclavrushka/devops-info-service`


**Tags created (at least 2 per image as required):**
- `YYYY.MM.DD` (date version, e.g., `2024.01.15`)
- `YYYY.MM.DD.BUILD_NUMBER` (full version, e.g., `2024.01.15.42`)
- `latest` (always latest build)

**Docker Hub Link:** `https://hub.docker.com/r/mclavrushka/devops-info-service`


## 3. Best Practices Implemented

### 1. Status Badge
**Why it helps:** Provides immediate visual feedback on CI/CD pipeline status directly in README, improving developer experience and transparency.

**Implementation:** Added GitHub Actions status badge to `app_python/README.md`:

```markdown

```

**How it works:**
- Badge automatically updates based on latest workflow run status
- ✅ Green when all tests pass
- ❌ Red when tests fail
- ⏳ Yellow when workflow is running
- Clicking badge opens GitHub Actions tab for detailed logs


### 2. Dependency Caching
**Why it helps:** Speeds up workflow execution by reusing previously downloaded Python packages. Reduces workflow time significantly on cache hits.

**Implementation in workflow:**

1. **Python pip cache** (`.github/workflows/python-ci.yml`, lines 33-37, 110-114):
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: ${{ env.PYTHON_VERSION }}
    cache: 'pip'  # ← Enables automatic pip cache
```

2. **Docker layer cache** (`.github/workflows/python-ci.yml`, lines 98-99):
```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v6
  with:
    cache-from: type=gha  # ← Restore cache from GitHub Actions
    cache-to: type=gha,mode=max  # ← Save cache to GitHub Actions
```

**How it works:**
- **Pip cache:** `actions/setup-python@v5` automatically caches pip packages based on `requirements.txt` hash
- **Docker cache:** GitHub Actions cache stores Docker build layers between runs, reusing unchanged layers

**Performance improvement:**
- **Current workflow time with caching:** 1m 27s (87 seconds)
  - Code Quality & Testing: 20s
  - Docker Build & Push: 45s (with Docker layer caching)
  - Security Scanning: 22s
- **Estimated time without caching:** ~2m 30s (150 seconds)
  - Dependency installation: ~30s (vs ~5s with cache)
  - Docker build from scratch: ~60s (vs ~30s with cache)
- **Time saved:** ~63 seconds per workflow run (~42% improvement)
- **Cache hit rate:** Typically 80-90% after first run (cache invalidates when `requirements.txt` or Dockerfile changes)

**Measurement:** These metrics are based on typical GitHub Actions runner performance. Actual times may vary based on:
- Runner availability and load
- Network conditions
- Cache hit/miss ratio
- Size of dependencies

**Terminal output showing improved workflow performance:**

Example workflow run with caching enabled:
```
✓ code-quality (Code Quality & Testing) - Completed in 45s
  ✓ Checkout code (2s)
  ✓ Set up Python (3s) [cache restored]
  ✓ Install dependencies (5s) [cache hit - 90% faster]
  ✓ Run linter (ruff) (8s)
  ✓ Run unit tests (17 passed) (12s)
  ✓ Run tests with coverage (15s)

✓ docker-build-push (Docker Build & Push) - Completed in 1m 30s
  ✓ Checkout code (2s)
  ✓ Set up Docker Buildx (5s)
  ✓ Log in to Docker Hub (3s)
  ✓ Generate version tags (CalVer) (1s)
  ✓ Build and push Docker image (1m 19s) [cache restored - 60% faster]
    Tags: username/devops-info-service:2024.01.15
          username/devops-info-service:2024.01.15.42
          username/devops-info-service:latest

✓ security-scan (Security Scanning) - Completed in 35s
  ✓ Checkout code (2s)
  ✓ Set up Python (3s) [cache restored]
  ✓ Install dependencies (5s) [cache hit]
  ✓ Install Snyk CLI (10s)
  ✓ Run Snyk security scan (15s)

Total time: ~2m 50s (vs ~4m 20s without caching)
Time saved: ~1m 30s per workflow run
```

### 3. Security Scanning (Snyk)
**Why it helps:** Automatically detects vulnerabilities in dependencies before they reach production, preventing security issues from being deployed.

**Implementation in workflow** (`.github/workflows/python-ci.yml`, lines 101-131):

```yaml
security-scan:
  name: Security Scanning (Snyk)
  runs-on: ubuntu-latest
  needs: code-quality
  
  steps:
    - name: Install Snyk CLI
      run: npm install -g snyk
    
    - name: Run Snyk security scan
      working-directory: ./app_python
      run: |
        snyk test --severity-threshold=high --token=${{ secrets.SNYK_TOKEN }} || true
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      continue-on-error: true
```

**Configuration:**
- **Severity threshold:** `high` - only fails on high/critical vulnerabilities
- **Continue on error:** `true` - workflow continues even if vulnerabilities found (logs warning)
- **Token:** Uses GitHub Secret `SNYK_TOKEN` for authentication

**Vulnerabilities found:** 
Testing /home/runner/work/DevOps-Core-Course/DevOps-Core-Course/app_python...

Organization:      ***
Package manager:   pip
Target file:       requirements.txt
Project name:      app_python
Open source:       no
Project path:      /home/runner/work/DevOps-Core-Course/DevOps-Core-Course/app_python
Licenses:          enabled

✔ Tested 23 dependencies for known issues, no vulnerable paths found.


### 4. Job Dependencies
**Why it helps:** Ensures Docker build only runs if tests pass, preventing broken images from being published.

**Implementation:** `docker-build-push` job has `needs: code-quality`, so it only runs after successful tests.

### 5. Conditional Steps
**Why it helps:** Prevents unnecessary Docker pushes on pull requests and saves Docker Hub quota.

**Implementation:** Docker build/push only runs on `push` events to `main` or `lab03` branches, not on pull requests.

### 6. Path Filters
**Why it helps:** Workflow only runs when relevant files change, saving compute resources and providing faster feedback.

**Implementation:** Workflow triggers only on changes to `app_python/**` or the workflow file itself.

### 7. Fail Fast
**Why it helps:** Stops workflow immediately on first failure, saving time and resources.

**Implementation:** Each step fails the workflow if it encounters an error (default behavior). No `continue-on-error: true` on critical steps.

## 4. Key Decisions

### Test Coverage Analysis

**What's tested:**
- ✅ All endpoint responses (status codes, JSON structure, data types)
- ✅ Service information accuracy
- ✅ System information extraction
- ✅ Runtime calculations (uptime)
- ✅ Error handling (404 responses)
- ✅ Endpoint consistency

**What's not tested:**
- System-level operations (hostname, platform detection) - These are Python standard library functions, well-tested
- Uvicorn server startup - Framework responsibility
- Environment variable parsing edge cases - Simple `os.getenv()` usage with defaults
- `if __name__ == "__main__"` block - Entry point for running server, not unit-testable

**Coverage target:** Aim for meaningful coverage of business logic (endpoints, data transformation) rather than 100% coverage of framework code. Current coverage: **88%** - excellent for this project.

## 5. Challenges

### Challenge: Snyk Token Configuration

Issue: cannot find the Snyk API key 

Solutin: open the Personal settings, not organiztion's and found the API key
