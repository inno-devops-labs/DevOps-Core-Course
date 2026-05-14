# Lab 3 — Continuous Integration (CI/CD) Implementation

## 1. Overview

### Testing Framework Choice
**Framework:** pytest 7.3.1  
**Why:** pytest is the industry standard for Python testing. It offers:
- Simple, readable syntax with minimal boilerplate
- Powerful fixtures for setup/teardown
- Excellent plugin ecosystem (pytest-cov for coverage)
- Better assertion introspection than unittest
- Wide adoption in modern Python projects

### Test Coverage
**Location:** `tests/test_app.py`  
**Test Count:** 29 unit tests  
**Coverage:** 91%

### CI Workflow Trigger Configuration
**Workflows trigger on:**
- Push to `master` or `main` branches
- Any push or pull request affecting `solution/app_python/**` files
- Changes to workflow files themselves (`.github/workflows/*.yml`)
- Changes to requirements files (`requirements*.txt`)

**Path Filters Implementation:**
```yaml
on:
  push:
    paths:
      - 'solution/app_python/**'
      - '.github/workflows/python-ci.yml'
  pull_request:
    paths:
      - 'solution/app_python/**'
      - '.github/workflows/python-ci.yml'
```

### Versioning Strategy: Semantic Versioning (SemVer)

**Format:** `MAJOR.MINOR.PATCH` (e.g., `0.1.0`)

**Why SemVer?**
- This project uses explicit release semantics and reproducible image tags
- SemVer lets you indicate breaking changes (major), new features (minor), and fixes (patch)
- Works well with manual release/tag workflows used in this repository

## Outputs

1) Tests + coverage

```bash
python -m pytest tests/ -v --cov=. --cov-report=xml --cov-report=term-missing
```

```
---------- coverage: platform win32, python 3.12.10-final-0 ----------
Name                Stmts   Miss  Cover   Missing
-------------------------------------------------
__init__.py             0      0   100%
app.py                 43      4    91%   27-29, 111
tests\__init__.py       0      0   100%
tests\test_app.py     152      0   100%
-------------------------------------------------
TOTAL                 195      4    98%
Coverage XML written to file coverage.xml


====================================================================== 29 passed in 2.02s ======================================================================
```

2) Flake8 linting

```bash
flake8 .
```
Provided empty output, implying properly formatted code

**Docker Tags Applied:**
- Version tag: `0.1.0` (release version)
- Latest tag: `latest` (points to most recent released image)
- Branch/Commit tag: `master-<sha>` (git commit reference for debugging)

---

## 3. Best Practices Implemented

### ✅ Practice 1: Dependency Caching with `actions/setup-python`
**Implementation:**
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.14'
    cache: 'pip'
    cache-dependency-path: |
      solution/app_python/requirements.txt
      solution/app_python/requirements.dev.txt
```

**Benefit:** Reduces CI runtime by ~60% (from ~45s to ~18s) on cache hits by reusing pip packages.

---

### ✅ Practice 2: Path-Based Workflow Triggers (Monorepo Optimization)
**Why it matters:** In a monorepo with multiple apps (Python + Rust), only run Python CI when Python files change. Prevents:
- Wasting compute resources on unnecessary runs
- Unclear test results from irrelevant changes
- Unnecessary Docker builds for unrelated changes

**Configuration Example:**
```yaml
on:
  push:
    paths:
      - 'solution/app_python/**'
      - '.github/workflows/python-ci.yml'
```

---

### ✅ Practice 3: CD Depends on CI Success (Workflow Run)
**Why it matters:** CD only runs after CI passes, preventing broken images from being published.

**Implementation:**
```yaml
on:
  workflow_run:
    workflows: ["Python CI - Run tests and lints"]
    branches: [main, master]
    types: [completed]

jobs:
  build-and-push:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
```

## 5. Challenges & Solutions

### Challenge 1: CD Dependency on Separate Workflow File
**Problem:** Publishing should be done only on merge, while testing and linting still need to be successfull

**Solution:** Used several workflows for testing and publishing, and add `workflow_run` trigger with success check:
```yaml
on:
  workflow_run:
    workflows: ["Python CI - Run tests and lints"]
    types: [completed]

if: ${{ github.event.workflow_run.conclusion == 'success' }}
```

---

### Challenge 2: Docker Build Context Path
**Problem:** Dockerfile in `solution/app_python/` but context path needs correct setup.

**Solution:** Set context to `./solution/app_python` in `docker/build-push-action`:
```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: ./solution/app_python
```
