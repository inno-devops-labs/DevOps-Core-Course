# LAB03 — Continuous Integration (CI/CD)

## 1. Unit testing
### 1.1 Testing framework choise
To complete this lab I selected **pytest**:
- Supports fuxtures
- Simple to use
- Easilly integrates with Flask

#### 1.2 Tests structure explanation:
- `test_root_endpoint_success`: Verifies GET / returns 200 status, checks complete JSON structure (service, system, runtime, request, endpoints fields), validates data types (str, int, list), and mocks uptime/system_info for consistent testing.
- `test_health_endpoint_success`: Tests GET /health returns 200 status, confirms health JSON structure (status, timestamp, uptime_seconds), verifies string/integer data types.
- `test_nonexistent_endpoint_404`: Ensures non-existent endpoint /nonexistent returns 404 status with correct error JSON structure ("Not Found" message).
- `test_root_wrong_method_404`: Confirms POST to root / (unsupported method) returns 404 status code.
- `test_health_wrong_method_405`: Verifies POST to /health (unsupported method) returns 404 status code.
- `test_unsupported_methods_405`: Parametrized test checking PUT, DELETE, PATCH methods on various endpoints all return 404 status.
- `test_empty_request_data`: Edge case test ensuring basic GET / works without additional request data, validates client_ip presence in response.
- `test_with_headers`: Edge case testing custom User-Agent header, confirms request parsing correctly extracts and returns header value in JSON.

#### 1.3 Running tests locally
Execute (in main project directory)
```bash
pytest
```
All test should pass
![all tests passing](./screenshots/lab3/tests.png)

### 2 CI Workflow
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
