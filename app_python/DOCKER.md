# Docker

## Dockerfile

The application is containerized with Docker using the following image:

```dockerfile
FROM python:3.12-alpine3.20
```

A fixed Python and Alpine version is used instead of a floating tag.

## Best practices used

### Non-root user

The container runs the application as `appuser`, not as `root`:

```dockerfile
RUN addgroup -S appgroup \
    && adduser -D -h /home/appuser -G appgroup appuser

USER appuser
```

The user's home directory is used as the working directory:

```dockerfile
WORKDIR /home/appuser
```

### Specific files are copied

The image does not copy the whole project directory. Only files required to run the application are copied:

```dockerfile
COPY --chown=appuser:appgroup requirements.txt .
COPY --chown=appuser:appgroup app.py .
```

### Layer order

Dependencies are copied and installed before the application code:

```dockerfile
COPY --chown=appuser:appgroup requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appgroup app.py .
```

This keeps dependency installation in a separate layer.

### No pip cache

Python packages are installed without storing the pip cache:

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

### .dockerignore

The `.dockerignore` file excludes files that are not required for building the image:

```dockerignore
venv/
__pycache__/
*.pyc
gunicorn.ctl
```

## Build

```bash
docker build -t moscow-time-app:1.0.0 .
```

## Run

```bash
docker run --rm -d --name moscow-time-app -p 8080:8080 moscow-time-app:1.0.0
```

## Check

```bash
curl http://localhost:8080
```

```bash
docker exec moscow-time-app id
```

The `id` command must show that the user id is not `0`.

## Stop

```bash
docker stop moscow-time-app
```
