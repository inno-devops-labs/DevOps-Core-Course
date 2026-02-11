# LAB03 — CI/CD with GitHub Actions

## 1. Overview

- Testing framework: **pytest**
  - Chosen for simple syntax and good Flask integration.
- Linting tool: **ruff**
  - Fast Python linter, easy to integrate in CI.
- CI: GitHub Actions
  - Runs on push and pull request for `app_python/**`
- Versioning strategy: **Calendar Versioning (CalVer)**
  - Format: `YYYY.MM.<run_number>`
  - Also tags image as `latest`
- Docker image:
  - `<your-dockerhub-username>/devops-info-service`

---

## 2. Local Testing

Run locally:

```bash
cd app_python
pip install -r requirements.txt
ruff check .
pytest -q
```

Example output:

`3 passed in 0.24s`

---

## 3. Workflow Evidence

- ✅ Tests and lint pass in GitHub Actions
    
- ✅ Docker image built and pushed automatically
    
- ✅ Tags created:
    
    - `YYYY.MM.<run_number>`
        
    - `latest`
        
- ✅ CI status badge added to README
    

---

## 4. CI Best Practices Implemented

- **Dependency caching** (`cache: pip`)  
    Speeds up repeated workflow runs.
    
- **Job dependency (`needs`)**  
    Docker build runs only if tests and lint pass.
    
- **Path filters**  
    Workflow runs only when `app_python/**` changes.
    
- **Concurrency cancel**  
    Cancels outdated runs on same branch.
    

---

## 5. Key Decisions

### Why CalVer?

This project is a service (not a library), so breaking changes are not critical for version communication.  
CalVer makes versioning simple and automatically generated in CI.

### Docker Tags

- `YYYY.MM.<run_number>`
    
- `latest`
    

### What is tested?

- `GET /`
    
- `GET /health`
    
- 404 error handling
    
- JSON response structure