# Lab 3 — Continuous Integration (CI/CD)

## Bonus Task — Multi-App CI & Test Coverage

### Multi-App CI

Created a separate workflow for Go app: `.github/workflows/go-ci.yml`.

**Path filters**:

- Python workflow runs only when `app_python/` changes.
- Go workflow runs only when `app_go/` changes.

This ensures that workflows are triggered selectively and independently, saving CI resources and avoiding unnecessary builds.

### Go Workflow

- Uses official `actions/setup-go@v4`
- Runs `go test ./... -v -cover` for unit tests
- Docker build and push with CalVer (`YYYY.MM`) and `latest` tags

**Docker tags created**:

- `sfedbro/app_go:2026.02`
- `sfedbro/app_go:latest`

### Test Coverage

Coverage reports generated using Go's `-coverprofile` and optionally uploaded to Codecov.

**Coverage badge** added to README shows current coverage percentage.

### Benefits of Path-Based Triggers

- Reduces unnecessary workflow runs
- Optimizes CI pipeline time
- Keeps multi-app monorepo CI organized and efficient
- Allows Python and Go workflows to run in parallel without interfering

### Workflow Proof

- Both Python and Go workflows run independently and successfully in GitHub Actions
- Only triggers for relevant changes in respective directories
- Docker images for Go app successfully built and pushed
- Coverage reports uploaded to Codecov

### Path Filters — Proof of Selective Triggering

The workflows were tested to ensure selective triggering:

- Change in `app_go/` triggered ONLY Go CI workflow
- Change in `app_python/` triggered ONLY Python CI workflow
- Change in root `README.md` did NOT trigger any workflow

This proves correct path-based filtering for monorepo setup.
