## Unit Testing

- Create unit tests for `app.py`
- Added to requirements.txt new libs
```txt
flask==3.1.0
pytest==8.2.2
pytest-cov==5.0.0
ruff==0.6.9
```
- Checked it tests locally. 

![pytest-local-result](screenshots/pytest_local_result.png)

## Github Action CI workflow

- `python-ci.yml` triggered only in `lab3` and `master` branches. Because in the CI/CD I push docker image to the docker hub, but in docker hub must be only latest and working, in good practise master always has working and latest code. And docker image pushed to the docker hub only from the `master` branch.
- As actions I choose basic actions what I always use then create CI/CD pipelines.
- As tagging of images I use Calendar Versioning. Because this stragegy is usefull and if in developing process we notice what some part of app is down by this tag we can find there it will down.

- **Link to passed CI/CD:** https://github.com/setterwars/DevOps-Core-Course/actions/runs/21708886646
![image-from-github](screenshots/image-from-github.png)

As you can see CD job is skiped because it run only then we pushed something on main because in the docker hub we want see only the latest version of application.

## Best practice CI/CD pipeline 

- Created Pipeline Budget in `app_python/README.md`
![pipeline-budget](screenshots/image.png)
- Added caching in python libs
- Try to add Synk but in proccess notice what sync now need paiment sub so used free pip-audit and found one lib with vulnerability. flask 3.1.0 changed to flask 3.1.1
- CalVer tagging in Docker Images 
- auto pushing in docker hub
- non breacking scanning
- verified action 
- CI/CD separation

![flask](screenshots/found-flask-error.png)

![pipeline-with-best-practice](screenshots/pipeline-with-best-practice.png)