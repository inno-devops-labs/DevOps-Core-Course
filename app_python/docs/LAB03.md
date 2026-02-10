## Overview
Pytest was chosen because it has simple syntax and is well suited for testing Flask applications.
The CI workflow runs on push and pull requests to app_python/.
Calendar Versioning was used because this is a continuously deployed service.

## Workflow Evidence
- GitHub Actions: green successful run
- Docker Hub: image published with tags `latest` and `2026.02`
- Local tests: pytest passed successfully

## Best Practices Implemented
- Dependency caching to speed up CI runs
- Fail fast strategy: Docker build runs only after tests pass
- Secrets used for Docker Hub authentication

## Challenges
- Initial test client setup for Flask
- Fixing import paths for pytest
- Docker authentication in CI
- The issue occurred because pytest was executed using the global installation instead of the virtual environment. Running tests via python -m pytest ensured correct dependency resolution.