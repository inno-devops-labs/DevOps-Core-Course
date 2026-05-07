# Lab 02

# Overview
## Choosing a Testing Framework
I choosed to use `pytest`, because I already a little bit familiar with it. In this semester, but in different course we studied it too, so I will use it here to practice more.

## Test structure explanation
1. Make a test client
2. Request all pathes (health, default and error)
3. Fully check presence of each response section on all depths. Also check types where possible

## Workflow trigger strategy
The workflow will trigger on every push into lab** branches. Since in this course we need to push only there, it is more than okay practice. After each last (or even single) push to lab**, we make to PRs, so it is not so good to start workflow again 2 times.

## Docker tagging strategy
I choose "Option B: Calendar Versioning (CalVer)" with format: "YYYY.MM.DD", so I can easily distinguish each versions: newer date - newer assignment. Also, when I will do lab assignment and make some really small changes in one day - I will save only last version with all fixes and bugs found. Also, I ofcourse use `latest` tag

# Workflow Evidance
## Successful workflow run
https://github.com/SamuelAnton/DevOps-Core-Course/actions/runs/21873318288

## Tests passing locally
### Terminal output
```sh
damir@damir-VB:~/Desktop/DevOps/DevOps-Core-Course/app_python$ pytest .
============================================= test session starts ==============================================
platform linux -- Python 3.10.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/damir/Desktop/DevOps/DevOps-Core-Course/app_python
collected 3 items                                                                                              

tests/test_app.py ...                                                                                    [100%]

============================================== 3 passed in 0.30s ===============================================
```

## Docker image on Docker Hub
https://hub.docker.com/r/damirsadykov/devops-info-service

## Status badge working in README
See the README file for python app, or:
[![Python test and build](https://github.com/SamuelAnton/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab03)](https://github.com/SamuelAnton/DevOps-Core-Course/actions/workflows/python-ci.yml)



# Best Practices Implemented
## Job Dependencies
There are 3 steps in CI workflow:
- Testing that application is working correctly + Security check with Snyk
- Docker build and push to DockerHub

This means, that if some test failed or security is low, we wouldn't build and push container

## Workflow Concurrency
I added this:
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```
So, if there will be queue to execution the workflow, only latest will run and rest will be canceled.

## Environment Variables
I use this env variables for repeated values, so I can change them in 1 place, to apply changes in all places:
- PYTHON_VERSION: '3.12'
- DOCKER_IMAGE_NAME: 'devops-info-service'
- APP_PATH: 'app_python'

## Caching
### Speed improvement with caching
- Before caching: test stage take 10-16s
- After caching: test stage take 9s

## Snyk
Found that `Flask==3.1.0` is vulnaruble. So I updated to `Flask==3.1.1`.

# Key Decisions
## Versioning Strategy
I choose "Option B: Calendar Versioning (CalVer)" with format: "YYYY.MM.DD", so I can easily distinguish each versions: newer date - newer assignment. Also, when I will do lab assignment and make some really small changes in one day - I will save only last version with all fixes and bugs found. Also, I ofcourse use `latest` tag

## Docker Tags
- latest
- date tag in format: "YYYY.MM.DD"

## Workflow trigger strategy
The workflow will trigger on every push into lab** branches. Since in this course we need to push only there, it is more than okay practice. After each last (or even single) push to lab**, we make to PRs, so it is not so good to start workflow again 2 times.

## Test Coverage
2. Request all pathes (health, default and error)
3. Fully check presence of each response section on all depths. Also check types where possible