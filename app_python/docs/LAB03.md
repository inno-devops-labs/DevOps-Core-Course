# Unit Testing

## Testing framework choice and why
After reviewing popular Python testing frameworks (such as `unittest` and `pytest`), I chose **pytest** because it makes writing, maintaining, and scaling tests easier and faster for both small and large projects.

### 1) Less boilerplate, faster to write tests
With `pytest`, you don’t need to create test classes or inherit from special base classes (which is common in `unittest`).  
Simple functions named `test_*` are enough, which keeps tests clean and easy to read.

### 2) Powerful fixture system
`pytest` provides a strong **fixture** mechanism for setting up test data and environments:
- reusable setup/teardown logic;
- flexible scopes (`function`, `module`, `session`);
- dependency injection by simply adding parameters to test functions.

This reduces duplication and improves test structure.

### 3) Easy test parametrization
`pytest` makes it simple to run the same test with multiple input datasets using parametrization.  
That improves coverage without copying and pasting similar tests.

### 4) Clear, helpful failure output
When a test fails, `pytest` produces detailed and readable error messages (including smart value comparisons).  
This speeds up debugging and helps quickly identify what went wrong.

### 5) Rich plugin ecosystem and CI integration
`pytest` has a large ecosystem of plugins and integrates well with:
- coverage tools,
- linters,
- CI/CD systems (GitHub Actions, GitLab CI, etc.),
- reporting tools.

This is useful if the project grows or needs automation.

### 6) Flexibility and compatibility
`pytest` can also run tests written in the `unittest` style, so it’s easier to adopt gradually.  
At the same time, `pytest` offers more modern and flexible features for everyday testing.

---

**Conclusion:** I chose **pytest** because it reduces boilerplate, provides powerful fixtures and parametrization, offers excellent debugging output, and scales well with plugins and CI workflows.

## Test structure explanation

All tests are located in `app_python/tests/` and are written with **pytest** using FastAPI’s `TestClient`.

### Directory layout
```text
app_python/
  app.py
  tests/
    conftest.py
    test_root.py
    test_health.py
    test_errors.py
```

### What each file contains
- `conftest.py`
  - Defines shared pytest fixtures (e.g., `client`) used across multiple test files.
  - The `client` fixture creates a `TestClient(app)` so tests can call the API endpoints without running a real server.
- `test_root.py`
  - tests the main endpoint `GET /`.
  - Verifies:
    - HTTP status code is `200`
    - JSON response contains required top-level fields (`service`, `system`, `runtime`, `request`, `endpoints`)
    - Nested fields exist and have reasonable types/values (e.g., `uptime_seconds` is an `integer`, `timezone` is `"UTC"`)
    - The endpoints list contains expected endpoints (`/` and `/health`)
- `test_health.py`
  - Tests `GET /health`.
  - Verifies:
    - HTTP status code is `200`
    - JSON response contains required fields (`status`, `timestamp`, `uptime_seconds`)
    - status is `"healthy"` and `timestamp` is serialized as an ISO string
- test_errors.py
  - Tests custom error handling:
    - **500 Internal Server Error**: adds a temporary endpoint that raises `RuntimeError` and checks that the response JSON matches the global exception handler.
    - **404 Not Found**: requests a non-existent endpoint and checks the custom 404 JSON. 
    - **Non-404 HTTPException**: adds a temporary endpoint that raises `HTTPException(418)` and checks the JSON returned by the `HTTPException` handler.
  - Temporary test routes are removed in `finally` blocks to avoid affecting other tests.

### Naming conventions
- Test files are named test_*.py
- Test functions are named test_*
- This allows pytest to automatically discover and run the test suite.

## How to run tests locally
Use command:
```bash
pytest
```

## Terminal output showing all tests passing
```bash
pytest
========================================== test session starts ===========================================
platform win32 -- Python 3.12.4, pytest-8.4.2, pluggy-1.6.0
rootdir: C:\Users\malov\PycharmProjects\DevOps-Core-Course
plugins: anyio-4.11.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 7 items                                                                                         

app_python\tests\test_errors.py ...                                                                 [ 42%]
app_python\tests\test_health.py ..                                                                  [ 71%]
app_python\tests\test_root.py ..                                                                    [100%]

=========================================== 7 passed in 0.48s ============================================
(.venv) PS C:\Users\malov\PycharmProjects\DevOps-Core-Course> 
```