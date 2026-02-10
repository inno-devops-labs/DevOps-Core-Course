# LAB03 - CI/CD (Python)

## 1. Overview
**Testing framework:** I used `pytest`. The syntax is clean, fixtures are easy to work with, and it is the default choice in most Python projects I see.

**What tests cover:** The tests hit `GET /`, `GET /health`, a 404 case, and helper functions like uptime formatting. I focused on structure and types instead of exact machine values.

**Workflow triggers:** CI runs on push and pull requests to `lab03`, `main`, or `master`, but only when `lab3c/app_python/**` or the workflow file changes.

**Versioning strategy:** I chose CalVer (YYYY.MM.DD). It is simple, and this service is released continuously rather than as a library.

## 2. Workflow Evidence
Add real links and outputs after you run CI:
- **Successful workflow run:** `<GitHub Actions URL>`
- **Tests passing locally:**
pytest
============================================================================================ test session starts ============================================================================================
platform win32 -- Python 3.12.2, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Users\Phoenix\PycharmProjects\DevOps\DevOps-CC\lab3c\app_python
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.0.0
collected 5 items                                                                                                                                                                                            

tests\test_app.py .....                                                                                                                                                                                [100%]

============================================================================================= 5 passed in 0.36s =============================================================================================
- **Docker image on Docker Hub:** `<Docker Hub URL>`
- **Status badge:** `<confirm badge works in README>`

## 3. Best Practices Implemented
- **Dependency caching:** `actions/setup-python` caches pip packages to speed up installs.
- **Job separation:** tests run in one job, Docker build/push depends on test success.
- **Conditional push:** Docker images only push on `push` events (not on PRs).
- **Concurrency:** newer runs cancel older runs for the same branch.
- **Path filters:** CI runs only when the Python app changes (monorepo friendly).
- **Snyk scanning:** dependency scan runs in CI (requires token).

Caching time saved:
```
<paste before/after timing notes or cache hit log>
```

Snyk result:
```
<paste snyk output or note "no vulnerabilities found">
```

## 4. Key Decisions
**Versioning Strategy:** CalVer fits a small service that ships frequently. It is easy to read and does not require manual version bumps.

**Docker Tags:** The workflow publishes `YYYY.MM.DD` and `latest` tags for the same image.

**Workflow Triggers:** I used path filters to avoid running Python CI when only Go code changes.

**Test Coverage:** Core endpoints and helper functions are tested. I did not try to cover every logging line.

## 5. Challenges (Optional)
- Everything was clear, because of experience of setting up CI/CD in my company workspace.
