
## Task — Multi-App CI with Path Filters + Test Coverage (2.5 pts)

### Part 1: Multi-App CI (1.5 pts)

#### Go CI Workflow Implementation

**File:** `.github/workflows/go-ci.yml`

**Workflow Structure:**
- **Code Quality & Testing:** Linting with `golangci-lint`, unit tests with `go test`
- **Docker Build & Push:** Multi-stage Docker build with CalVer versioning
- **Security Scanning:** Snyk integration for Go dependencies

**Key Features:**
- ✅ Language-specific linting (`golangci-lint`)
- ✅ Unit tests with coverage reporting
- ✅ CalVer versioning strategy (consistent with Python app)
- ✅ Docker layer caching via GitHub Actions cache
- ✅ Go module caching for faster builds

**Path Filters:**
```yaml
paths:
  - 'app_go/**'
  - '.github/workflows/go-ci.yml'
```

**Benefits of Path-Based Triggers:**
- **Resource Efficiency:** Python CI doesn't run when only Go code changes (and vice versa)
- **Faster Feedback:** Developers get faster CI results for their specific language
- **Parallel Execution:** Both workflows can run simultaneously when both apps change
- **Cost Savings:** Reduced GitHub Actions minutes usage

#### Test Coverage for Go Application

**Test Structure:**

Tests are organized into separate files following best practices:

```
app_go/
├── root_test.go      # Tests for GET / endpoint (7 tests)
├── health_test.go    # Tests for GET /health endpoint (2 tests)
├── errors_test.go    # Tests for error handling (404 responses) (1 test)
└── runtime_test.go   # Tests for runtime calculations (4 tests)
```

**Coverage:**
- ✅ Main endpoint (`GET /`) - JSON structure, service info, system info validation
- ✅ Health endpoint (`GET /health`) - Status, timestamp, uptime validation
- ✅ Error handling (404 responses)
- ✅ Runtime calculations (uptime formatting)
- ✅ Helper functions (`formatUptime`)
- ✅ Request info capture (method, user agent, path)
- ✅ System info details (platform, architecture)
- ✅ Multiple requests handling
- ✅ Endpoints list validation
- ✅ Error handling for `os.Hostname()` failure (hostname fallback to "unknown")

**Total:** 14 test functions covering all endpoints and core functionality

**Coverage:** 71.4% (exceeds CI threshold of 70%)
- `mainHandler`: 100% coverage (including error handling for `os.Hostname()`)
- **Note:** `main()` function (entry point) is not unit-testable and reduces total coverage
- **All testable functions are 100% covered:** `getRuntime`, `formatUptime`, `mainHandler`, `healthHandler`
- **Coverage breakdown:**
  - `getRuntime`: 100%
  - `formatUptime`: 100%
  - `mainHandler`: 100%
  - `healthHandler`: 100%
  - `main`: 0% (not unit-testable by design)

#### Workflow Parallelization

Both workflows (`python-ci.yml` and `go-ci.yml`) are configured to:
- Run independently based on path filters
- Execute in parallel when both apps change in the same commit
- Share Docker Hub credentials via GitHub Secrets
- Use consistent CalVer versioning strategy

**Evidence of Selective Triggering:**
- Python workflow only runs when `app_python/**` changes
- Go workflow only runs when `app_go/**` changes
- Both workflows run when their respective workflow files change
- Neither workflow runs when only documentation or other files change

**How to Test Path Filters:**

1. **Test Python workflow only:**
   ```bash
   # Make a change to Python app
   echo "# Test" >> app_python/app.py
   git add app_python/app.py
   git commit -m "test: trigger Python CI only"
   git push
   # Verify: Only python-ci.yml workflow runs
   ```

2. **Test Go workflow only:**
   ```bash
   # Make a change to Go app
   echo "// Test" >> app_go/main.go
   git add app_go/main.go
   git commit -m "test: trigger Go CI only"
   git push
   # Verify: Only go-ci.yml workflow runs
   ```

3. **Test both workflows:**
   ```bash
   # Make changes to both apps
   echo "# Test" >> app_python/app.py
   echo "// Test" >> app_go/main.go
   git add app_python/app.py app_go/main.go
   git commit -m "test: trigger both CI workflows"
   git push
   # Verify: Both workflows run in parallel
   ```

4. **Test no workflow triggers:**
   ```bash
   # Make a change to documentation only
   echo "# Test" >> README.md
   git add README.md
   git commit -m "docs: update README"
   git push
   # Verify: No workflows run
   ```

### Part 2: Test Coverage Badge (1 pt)

#### Codecov Integration

the connection for the website codecov.io is forbidden (403 error), so I cannot register and connect the repository there, but the other implementation is correct

**Implementation:**
- Coverage reports generated using `pytest-cov` with XML output
- Coverage uploaded to Codecov via `codecov/codecov-action@v4`
- Coverage badge added to `app_python/README.md`

**Coverage Metrics:**
- **Current Coverage:** 88%
- **Coverage Tool:** `pytest-cov` 5.0.0
- **Report Format:** XML (for Codecov) + HTML (for local viewing) + Terminal (for CI logs)

**What's Covered:**
- ✅ All endpoint handlers (`GET /`, `GET /health`)
- ✅ JSON response structure validation
- ✅ Error handling (404 responses)
- ✅ Runtime calculations (uptime, timestamps)
- ✅ Request information extraction

**What's Not Covered (and why):**
- System-level operations (`os.Hostname()`, `platform` module) - Standard library functions, well-tested
- Server startup (`uvicorn.run()`) - Framework responsibility
- Environment variable parsing - Simple `os.getenv()` with defaults

**Coverage Badge:**
```markdown
![Codecov](https://codecov.io/gh/McLavrushka/DevOps-Core-Course/branch/lab03/graph/badge.svg)
```

**Coverage Threshold:**
- **Threshold:** 70% minimum coverage enforced in CI
- **Implementation:** `--cov-fail-under=70` flag in pytest command
- **Behavior:** CI workflow fails if coverage drops below 70%
- **Current Coverage:** 88% (above threshold ✅)
- **Rationale:** 70% provides good balance between quality assurance and practical development

#### Benefits of Coverage Tracking

- **Visibility:** Immediate feedback on test coverage in README
- **Trend Tracking:** Codecov dashboard shows coverage trends over time
- **Quality Assurance:** Helps identify untested code paths
- **CI Integration:** Coverage reports available in GitHub Actions logs