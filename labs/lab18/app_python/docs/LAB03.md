# LAB03 — CI/CD with GitHub Actions

## 1. Overview

This lab implements a CI/CD pipeline for the **DevOps Info Service** using **GitHub Actions**.

- **Testing framework:** `pytest`
- **Linting:** `ruff`
- **Container build & publish:** Docker Buildx → Docker Hub
- **Security scanning:** Snyk CLI (dependency scan from `requirements.txt`)

### Testing framework choice

Two common Python testing frameworks were considered:

- **unittest** — built-in Python testing framework with class-based test structure.
- **pytest** — third-party framework with simpler syntax, fixtures, and better readability.

**Chosen framework: pytest**

**Justification:**
- simpler test syntax (plain functions instead of classes)
- powerful fixtures and ecosystem
- widely used in modern Python projects
- better failure output and developer experience
- easy integration with CI pipelines

For this project, pytest provides a clean and maintainable way to test API endpoints.

**What is tested:**
- `GET /` returns a valid JSON structure with required sections (`service`, `system`, `runtime`, `request`, `endpoints`)
- `GET /health` returns `"status": "healthy"` and includes `timestamp` and `uptime_seconds`
- unknown endpoints return a JSON 404 response

**Workflow triggers:**
- Runs on `push` and `pull_request` for branches `master` and `lab03`
- Runs only when files in `app_python/**` or the workflow file change (path filter)

**Versioning strategy (Docker tags):**
- **CalVer** tag: `YYYY.MM.DD-<shortSHA>` (traceable build version)
- Branch tag: `lab03` (easy to pull the latest build from this branch)

---

## 2. Workflow Evidence

### 2.1 GitHub Actions run
- Workflow file: `.github/workflows/python-ci.yaml`
- Successful run link: **<https://github.com/wkwtfigo/DevOps-Core-Course/actions/runs/21838910478>**

### 2.2 Test + lint output (CI)

![lint and test evidence](/app_python/docs/screenshots/lint+test.png)

### 2.3 Docker image publish
Docker Hub repository:
- `wkwtfigo/devops-info-service`
- URL: 
```text
https://hub.docker.com/r/wkwtfigo/devops-info-service
```

Published tags from CI:
- `lab03`
- `2026.02.09-1d708b5`

```bash
#21 pushing ***/devops-info-service:lab03 with docker
#21 pushing layer bf48bca45dca
#21 pushing layer 220bf4a7cb08
#21 pushing layer 473bf974db40
#21 pushing layer f73c1c8fba85
#21 pushing layer 96c05063c739
#21 pushing layer 241fcae5008f
#21 pushing layer 61e0df330e38
#21 pushing layer 1dfdd9260fd4
#21 pushing layer 0ae7ca672022
#21 pushing layer a8ff6f8cbdfd
#21 pushing layer 473bf974db40 512B / 42B 0.2s
#21 pushing layer bf48bca45dca 7.17kB / 4.72kB 0.3s
#21 pushing layer 473bf974db40 2.56kB / 42B 0.3s
#21 pushing layer f73c1c8fba85 1.65MB / 9.48MB 0.4s
#21 pushing layer 96c05063c739 11.78kB / 3.87kB 0.3s
#21 pushing layer f73c1c8fba85 5.40MB / 9.48MB 0.5s
#21 pushing layer 220bf4a7cb08 2.31MB / 38.07MB 0.5s
#21 pushing layer f73c1c8fba85 8.84MB / 9.48MB 0.6s
#21 pushing layer 220bf4a7cb08 8.64MB / 38.07MB 0.7s
#21 pushing layer f73c1c8fba85 9.49MB / 9.48MB 0.6s
#21 pushing layer 220bf4a7cb08 11.77MB / 38.07MB 0.8s
#21 pushing layer 220bf4a7cb08 14.52MB / 38.07MB 0.9s
#21 pushing layer 220bf4a7cb08 17.65MB / 38.07MB 1.0s
#21 pushing layer 220bf4a7cb08 20.40MB / 38.07MB 1.2s
#21 pushing layer 220bf4a7cb08 22.76MB / 38.07MB 1.3s
#21 pushing layer 96c05063c739 1.3s done
#21 pushing layer 220bf4a7cb08 26.30MB / 38.07MB 1.4s
#21 pushing layer 473bf974db40 1.3s done
#21 pushing layer bf48bca45dca 1.4s done
#21 pushing layer 220bf4a7cb08 33.37MB / 38.07MB 1.6s
#21 pushing layer 220bf4a7cb08 36.51MB / 38.07MB 1.7s
#21 pushing layer 220bf4a7cb08 38.92MB / 38.07MB 1.8s
#21 pushing layer f73c1c8fba85 2.1s done
#21 pushing layer 241fcae5008f 2.5s done
#21 pushing layer 220bf4a7cb08 3.1s done
#21 pushing layer 0ae7ca672022 5.9s done
#21 pushing layer 61e0df330e38 5.9s done
#21 pushing layer 1dfdd9260fd4 5.9s done
#21 pushing layer a8ff6f8cbdfd 5.9s done
#21 DONE 6.0s

#22 pushing ***/devops-info-service:2026.02.09-1d708b5 with docker
#22 pushing layer a8ff6f8cbdfd 1.9s done
#22 pushing layer bf48bca45dca 1.9s done
#22 pushing layer 220bf4a7cb08 1.9s done
#22 pushing layer 473bf974db40 1.9s done
#22 pushing layer f73c1c8fba85 1.9s done
#22 pushing layer 96c05063c739 1.9s done
#22 pushing layer 241fcae5008f 1.9s done
#22 pushing layer 61e0df330e38 1.9s done
#22 pushing layer 1dfdd9260fd4 1.9s done
#22 pushing layer 0ae7ca672022 1.9s done
#22 DONE 1.9s
```

![docker hub](/app_python/docs/screenshots/dockerhub.png)

## 3. Best Practices Implemented
### 3.1 Separation of concerns (jobs)

- `test` job runs lint + unit tests
- `docker` job runs only after tests succeed (`needs: test`)
- Result: images are published only from verified code.

### Matrix testing

Tests run on Python 3.12 and 3.13, which increases confidence that the service works across supported versions.

### 3.3 Dependency caching

Dependency caching is implemented using `actions/setup-python` with pip cache enabled:

```yaml
cache: pip
cache-dependency-path:
  - app_python/requirements.txt
  - app_python/requirements-dev.txt
```

Cache behavior was verified using two workflow runs:
- Without cache: dependencies were downloaded from PyPI
- With cache: pip reused locally cached wheels ("Using cached ...")

In this project, dependency installation time remained around ~9 seconds in both cases because the dependency set is small and installs quickly.

However, caching still prevents repeated downloads and becomes significantly more beneficial for larger projects with heavy dependencies.

`pip` logs without cache:
```bash
Downloading httpx-0.28.1-py3-none-any.whl (73 kB)
Downloading httpcore-1.0.9-py3-none-any.whl (78 kB)
Downloading annotated_types-0.7.0-py3-none-any.whl (13 kB)
Downloading click-8.3.1-py3-none-any.whl (108 kB)
Downloading coverage-7.13.4-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (254 kB)
Downloading h11-0.16.0-py3-none-any.whl (37 kB)
Downloading httptools-0.7.1-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (517 kB)
Downloading idna-3.11-py3-none-any.whl (71 kB)
Downloading iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
Downloading packaging-26.0-py3-none-any.whl (74 kB)
Downloading pygments-2.19.2-py3-none-any.whl (1.2 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.2/1.2 MB 89.3 MB/s  0:00:00
Downloading python_dotenv-1.2.1-py3-none-any.whl (21 kB)
Downloading pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (807 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 807.9/807.9 kB 68.2 MB/s  0:00:00
Downloading typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Downloading typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Downloading uvloop-0.22.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (4.4 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.4/4.4 MB 118.8 MB/s  0:00:00
Downloading watchfiles-1.1.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (456 kB)
Downloading websockets-16.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (184 kB)
Downloading certifi-2026.1.4-py3-none-any.whl (152 kB)
```

`pip` logs with cache:
```bash
Using cached fastapi-0.115.0-py3-none-any.whl (94 kB)
Using cached uvicorn-0.30.6-py3-none-any.whl (62 kB)
Using cached pydantic-2.12.5-py3-none-any.whl (463 kB)
Using cached pydantic_core-2.41.5-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.1 MB)
Using cached starlette-0.38.6-py3-none-any.whl (71 kB)
Using cached anyio-4.12.1-py3-none-any.whl (113 kB)
Using cached pytest-9.0.2-py3-none-any.whl (374 kB)
Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
Using cached pytest_cov-7.0.0-py3-none-any.whl (22 kB)
Using cached ruff-0.15.0-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (11.1 MB)
Using cached httpx-0.28.1-py3-none-any.whl (73 kB)
Using cached httpcore-1.0.9-py3-none-any.whl (78 kB)
Using cached annotated_types-0.7.0-py3-none-any.whl (13 kB)
Using cached click-8.3.1-py3-none-any.whl (108 kB)
Downloading coverage-7.13.4-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (254 kB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Using cached httptools-0.7.1-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (517 kB)
Using cached idna-3.11-py3-none-any.whl (71 kB)
Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
Using cached packaging-26.0-py3-none-any.whl (74 kB)
Using cached pygments-2.19.2-py3-none-any.whl (1.2 MB)
Using cached python_dotenv-1.2.1-py3-none-any.whl (21 kB)
Using cached pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (807 kB)
Using cached typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Using cached typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Using cached uvloop-0.22.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (4.4 MB)
Using cached watchfiles-1.1.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (456 kB)
Using cached websockets-16.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (184 kB)
Using cached certifi-2026.1.4-py3-none-any.whl (152 kB)
```

### 3.4 Path filtering

Workflow runs only when app_python/** or the workflow file changes.
This avoids running CI for unrelated edits (docs/lectures/etc.).

### 3.5 Concurrency control

The workflow uses:

```yaml
concurrency:
  group: python-ci-${{ github.ref }}
  cancel-in-progress: true
```

This prevents wasting minutes on outdated runs when multiple commits are pushed quickly.

## 4. Security (Snyk)

Snyk is executed using the Snyk CLI and scans the runtime dependency file:

- Target file: `app_python/requirements.txt`
- Command:

```bash
snyk test --file=app_python/requirements.txt --severity-threshold=high --skip-unresolved
```

**Result:**

- Snyk findings: `0 high-severity vulnerabilities`
- Action taken:
    - No vulnerabilities were found in the project.
    
![snyk output](/app_python/docs/screenshots/snyk.png)

## 5. Key Decisions

- Ruff instead of flake8: faster and simpler configuration; good for CI.
- CalVer tags for Docker images: easy to see when an image was produced and link it to a commit (shortSHA).
- Tests validate JSON structure, not exact host values: values like `hostname` and platform differ between local machine and CI runner.

## 6. Challenges & Fixes
### 6.1 Workflow not triggering

**Cause:** incorrect path filter (`.yml` vs `.yaml`) prevented workflow changes from triggering runs.

**Fix:** updated paths to match the real filename: `.github/workflows/python-ci.yaml`.

### 6.2 Snyk action failing due to missing packages

**Cause:** `snyk/actions/python@master` runs in a container and didn’t see installed packages.

**Fix:** switched to Snyk CLI installed via `npm`, scanning `requirements.txt` directly.

### 6.3 Dependency separation

**Cause:** dev tools (pytest/ruff/httpx) were mixed into runtime requirements, increasing image size and scan noise.

**Fix:** split dependencies into:
- `requirements.txt` (runtime)
- `requirements-dev.txt` (dev/test tools)