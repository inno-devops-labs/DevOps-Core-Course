# LAB03 — Continuous Integration (CI/CD)

## 1. Overview

**Testing Framework:** pytest  
**Why:** Simple syntax, FastAPI TestClient works out of the box, minimal boilerplate, industry standard

**Tested endpoints:**
- `GET /` — status 200, JSON structure (service, system, runtime, request, endpoints), required fields (name, version)
- `GET /health` — status 200, fields: status="healthy", timestamp, uptime_seconds
- Error cases — 404 Not Found, 405 Method Not Allowed

**CI Workflow Triggers:**
- `push` to `main`, `master`, `lab*` branches
- `pull_request` to `main`/`master`
- No path filters (basic implementation)

**Versioning Strategy:** Calendar Versioning (CalVer)  
**Format:** `YYYY.MM.DD-RUN_NUMBER` (example: `2026.02.13-42`)  
**Why:** This is a web service with continuous deployment — build date gives more context than semantic versioning. Users need to know *when* it was built, not what breaking changes were introduced.

---

## 2. Workflow Evidence

### Successful workflow run

https://github.com/Amirhan-322/DevOps-Core-Course/actions/runs/21957444272

Also you can see done workflow in the screenshot `08-workflow-jobs-done.png`


### Tests passing locally

You can see the pytest output in the screenshot `09-pytest-output.png`

### Docker Hub images

