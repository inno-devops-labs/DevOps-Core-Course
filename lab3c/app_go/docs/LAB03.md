# LAB03 - CI/CD (Go Bonus)

## Multi-App CI Summary
I added a separate workflow for the Go app with its own path filters. This keeps Python and Go CI independent and avoids running jobs that are not needed.

## Path Filters
- Go workflow runs only when `lab3c/app_go/**` or its workflow file changes.
- Python workflow runs only when `lab3c/app_python/**` or its workflow file changes.

## Workflow Evidence
Add real links after CI runs:
- ✅ **Go workflow run:** `<paste GitHub Actions URL>`
- ✅ **Docker image on Docker Hub:** `<paste Docker Hub URL>`

## Notes
- Go CI uses `go test` and a basic lint step.
- Docker builds use the same CalVer tag scheme as Python.
