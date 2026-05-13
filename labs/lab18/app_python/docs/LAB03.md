# Documentation

## Overview

### Choose a Testing Framework

Since the project is quite simple, it is not a big difference between frameworks regarding their more complex features. I chose pytest because it is easy to use as a beginner and it provides all needed functionality.

### Test coverage & trigger configuration

- I check the structure of a json response for ./ and ./health requests, and additionally review error cases (response.status code is 404 or 500). Also, I test the type of the value for importand fields. 

- The pipeline is triggered on push and pull requests. It is useful for me since I can check the pipeline during working on the lab (pushes) and then on pull request for the submission.

### Versioning Strategy 

- latest tag

- I chose to use Calendar Versioning since it is quite indicative for the university course (I can easily determine the image corresponding to the particular lab (by the date)).

- Also I tag by commit SHA for needed image detection

## Workflow Evidence

### Tests terminal output

![Passed tests](./screenshots/lab03-shots/unit%20test%20output.png)

### Pipeline test with GitHub actions

[Successful run](https://github.com/ffountainer/DevOps-Core-Course/actions/runs/21885090766)

![](./screenshots/lab03-shots/pipeline%20success.png)

### GitHub Image

[Image](https://hub.docker.com/layers/fountainer/my-app/latest/images/sha256:ec4a12a2a6e91d464be4f1a908f23a3646ed05233d2ae82101357ea1e23bd677?uuid=8c4ce238-1b75-4c64-ba2e-b07167c9cb11%0A)

## Best Practices Implemented

- check on pull request to see the status before merging
- secrets for sensitive data
- docker image layer caching for quicker builds
- job dependencies (so docker build and push do not run if unit tests have not passed)
- add status badge to immediately see the current pipeline status
- dependency caching for quicker unit testing
- security scanning with Snyk for detecting vulnerabilities

![Improvements](./screenshots/lab03-shots/improved%20perf.png)

### Caching implementation and speed improvement metrics

Caching is enabled by actions/setup-python@v5 and Docker layer caching, reducing dependency installation and image rebuild times. This decreased average workflow time from ~2-1 min to ~1-0.4 min (~40–60% faster on subsequent runs).

![DockerHub images](./screenshots/lab03-shots/images%20with%20tags%20docker%20hub.png)

### Snyk integration

Initially there was a vulnerability with outdated flask version, so I upgraded it. 

## Key Decisions

### Versioning Strategy 

- I chose to use Calendar Versioning since it is quite indicative for the university course (I can easily determine the image corresponding to the particular lab (by the date)).

### Docker Tags

- CI creates CalVer, latest, and SHA tags.

### Workflow Triggers

- The pipeline is triggered on push and pull requests. It is useful for me since I can check the pipeline during working on the lab (pushes) and then on pull request for the submission.

### Test Coverage

I check the structure of a json response for ./ and ./health requests, and additionally review error cases (response.status code is 404 or 500). Also, I test the type of the value for importand fields. 

What is not tested:
    - if env variables provide correct values

### Chosen actions

- actions/checkout@v4: to check-out my repository under $GITHUB_WORKSPACE, so my workflow can access it

- actions/setup-python@v5: to install python and add it to path and to allow caching

- docker/login-action@v3: to login into docker

- docker/setup-buildx-action@v3: to enable layer caching 

- docker/build-push-action@v5: to build and push image

## Challenges

- didn't work with unit testing and assert command before
- snyk didn't find my files so I stopped using snyk action and configured job manually