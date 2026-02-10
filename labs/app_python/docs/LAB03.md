#### Overview ####

- I use pytest as a testing framework because I already had experience with it.

- I check that both endpoints returns correct data.

- CI workflow runs on pull-requests in main and on pushes in all branches. It was done that way, because for every new lab I create new branch, but I don't merge it back with main branch after lab is done.

- Calendar versioning is used, because updates tend to appear every week as course progresses

#### Successful Workflow run ####

https://github.com/TheVex/DevOps-Core-Course/actions/runs/21882181586

#### Test passing ####

```bash
========================================= test session starts ==========================================
platform win32 -- Python 3.11.1, pytest-8.3.5, pluggy-1.6.0
rootdir: C:\Users\Vexell\PycharmProjects\DevOps-Core-Course\labs\app_python
plugins: anyio-4.12.1
collected 3 items

tests\test_invalid_get.py .                                                                       [ 33%]
tests\test_valid_get.py ..                                                                        [100%]

========================================== 3 passed in 0.19s =========================================== 

```

#### Docker Image ####

https://hub.docker.com/layers/thevex/simple-app/2026.02.10/images/sha256:023c192ec5b8142987dfd40e5cf4cbb767729825deddd0c4cf5dc56cb64cdf7e?uuid=BDC64712-7BF3-4D49-8FFD-64109A7DF787

#### Practices ####

1) Fail Fast - no need in processing all pipeline if its already has error.
2) Job Dependencies - similarly to Fail Fast: tests aren't succeed, so you should not create an image.
3) Pull Request Check - to make sure that unnsafe code will not appear in main branch
4) Caching: Installing requirements took 44 seconds before caching and only 5 seconds after.
5) No vulnerabilities were found.

#### Key Decisions ####

- Calendar versioning is used, because updates tend to appear every week as course progresses, so I find it convenient to use this type of versioning.

- CI creates latest and calendar version tags.

- CI workflow runs on pull-requests in main and on pushes in all branches. It was done that way, because for every new lab I create new branch, but I don't merge it back with main branch after lab is done.

- I tested existence of endpoints and check if they contain information that generally is static. It is not easy to test dynamic information, so it wasn't covered.
