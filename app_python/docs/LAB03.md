# LAB 03 — DevOps Info Service (CI/CD)

## Overview
- **Testing framework:** pytest (simple syntax, fast testing, good FastAPI support).
- **What is tested:** `/`, `/health`, 404 handler and 500 handler.
- **CI goal:** triggers on push to `main` or `lab3` branches. Runs only when updater files connected with app (.py files, requirements.txt, Dockerfile, python-ci.yml)
- **Versioning:** CalVer (`YYYY.MM.DD` + `latest`). Easy to implement and undestand when image was created.


## Workflow Evidence
**Successful workflow run**: https://github.com/Chaleshka/DevOps-Core-Course/actions/runs/21883290397
**Tests passing locally**:
=================================== test session starts ====================================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0
rootdir: G:\DevOps\DevOps-Core-Course\app_python
plugins: anyio-4.9.0, langsmith-0.3.15
collected 4 items                                                                           

tests\test_app.py <span style="color:green">.... [100%]</span>

<span style="color:green">==================================== 4 passed in 0.44s =====================================</span>

**Docker Hub image**: https://hub.docker.com/layers/chaleshka/devops-info-service/2026.02.10/images/sha256-aec5bb631045a09b34aa37175e252dc82172dec8214e31d0e8a12365b3dcdc5e
**Status badge visible**: [![Workflow](https://github.com/Chaleshka/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab3)](https://github.com/Chaleshka/DevOps-Core-Course/actions/workflows/python-ci.yml). Its also shown on [README.md](/app_python/README.md)


## Best Practices Implemented
- **Path filters**: We looking only for paths, that are connected with project. If we update, for example md file, we don't need to run workflow.
- **Snyk security scanning**: Check dependencies for security. If there is problem we will unpossible to upload this app.
- **Fail fast**: Firstly we check tests, linker and synk. If something fail, application will not be uploaded.
- **Dependency caching**: While there is no changes in requirements.txt, every next run will be faster.
- **Envirements usage**: We don't use secret information or general variables for every workflow. We set it once into repository envirement space and use it everywhere.

### Caching metrics
- Before: ~1m 
- After: ~50s

### Snyk results
- Vulnerabilities found: no
- Actions taken: none


## Key Decisions
- **Versioning Strategy**: Chose **CalVer** because this is easy to implement
- **Docker Tags**: For my application 
    - `chaleshka/devops-info-service:<YYYY.MM.DD>` (version)
    - `chaleshka/devops-info-service:latest`
    - `DOCKERHUB_USERNAME/application name:<tag/version>` (general for any image)
- **Workflow Triggers**: We will run workflows when there is push only on `lab3` branch. We will not run workflow if there is push to any other branch. (`lab3` like `dev` branch and `master` realese branch. After success workflow wa can make pull request to merge code with `master` branch)
- **Test Coverage**: Covered every main endpoint and every handled error.