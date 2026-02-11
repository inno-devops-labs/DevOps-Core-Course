# LAB03 — Continuous Integration (CI/CD)

## 1. Overview
### 1.1 Testing framework choise
To complete this lab I selected **pytest**:
- Supports fuxtures
- Simple to use
- Easilly integrates with Flask

### 1.2 Tests coverage
Tests cover:
- GET /
- GET /health
- Status codes
- JSON responses

### 1.3 CI Workflow
CI workflow triggers on:
- push to app_python/**
- pull requests

It performs:
1. Linting (ruff)
2. Testing (pytest)
3. Coverage generation
4. Docker build & push
5. Snyk security scan


## 2. Versioning Strategy
I chose **CalVer** using GitHub run number:

Tags:
- `latest`
- `${{ github.run_number }}`

Reason:
- simple
- automatic
- ideal for continuous deployment


## 3. Best Practices Implemented
- **Fail-fast:** workflow stops on first error  
- **Caching:** pip cache via setup-python  
- **Concurrency:** cancels outdated runs  
- **Security scanning:** Snyk  
- **Path filters:** workflow runs only for app_python  


## 4. Evidence
- All tests pass locally  
- Workflow runs successfully  
- Docker Hub shows versioned images  
- README badge works  

---

## 6. Challenges
- Understanding path filters  
- Fixing Docker Hub authentication  
- Adding Snyk token  
