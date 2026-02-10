# LAB03 — Continuous Integration (CI/CD)

## Task 1 — Unit Testing

### Testing Framework Selection
**Choice:** `pytest`

**Why pytest:**
- **Simple syntax**: readable tests with minimal boilerplate.
- **Great ecosystem**: fixtures (`client`), monkeypatching, plugins.
- **Works well with Flask**: integrates cleanly with Flask’s built-in test client.

### Test Structure
- Tests are located in `app_python/tests/`
- Main test file: `app_python/tests/test_endpoints.py`
- Covered cases:
  - `GET /` — JSON structure and required fields
  - `GET /health` — health response fields
  - `404` — JSON error response for unknown endpoint
  - `500` — JSON error response on internal exception

### How to Run Tests Locally
Install dev dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

### Pytest Output (Proof)

```text
MojPK@MacBook-Pro-168 app_python % pytest
========================================================== test session starts ===========================================================
platform darwin -- Python 3.13.1, pytest-8.3.4, pluggy-1.6.0
rootdir: /Users/MojPK/Downloads/University/DevOps/DevOps-Core-Course/app_python
plugins: anyio-4.9.0
collected 4 items

tests/test_endpoints.py ....                                                                                                       [100%]

=========================================================== 4 passed in 0.08s ============================================================
```

### Screenshot

![Pytest output](screenshots/04-pytest-output.png)


