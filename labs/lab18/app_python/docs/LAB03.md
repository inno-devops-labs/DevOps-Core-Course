# LAB03 — Continuous Integration (CI/CD)

## 1. Testing Framework Choice
I selected **pytest** because:
- it has simple syntax
- supports fixtures
- integrates with FastAPI test client
- works well with coverage tools

Tests cover:
- GET /
- GET /health
- JSON structure
- status codes

To run tests locally:
```bash
pytest
```

---

## 2. CI Workflow Overview
My CI workflow runs on:
- push to app_python/**
- pull requests

It performs:
1. Linting (ruff)
2. Testing (pytest)
3. Coverage generation
4. Docker build & push
5. Snyk security scan

---

## 3. Versioning Strategy
I chose **CalVer** using GitHub run number:

Tags:
- `latest`
- `${{ github.run_number }}`

Reason:
- simple
- automatic
- ideal for continuous deployment

---

## 4. Best Practices Implemented
- **Fail-fast:** workflow stops on first error  
- **Caching:** pip cache via setup-python  
- **Concurrency:** cancels outdated runs  
- **Security scanning:** Snyk  
- **Path filters:** workflow runs only for app_python  

---

## 5. Evidence
- All tests pass locally  
- Workflow runs successfully  
- Docker Hub shows versioned images  
- README badge works  

---

## 6. Challenges
- Understanding path filters  
- Fixing Docker Hub authentication  
- Adding Snyk token  
