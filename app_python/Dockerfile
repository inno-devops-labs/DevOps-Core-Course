# syntax=docker/dockerfile:1
FROM python:3.13-slim

# Security / correctness defaults for Python in containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-root user (mandatory)
# Fixed UID/GID helps in CI and when mounting volumes.
RUN groupadd --gid 10001 appuser \
 && useradd  --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin appuser \
 && mkdir -p /app/data /config \
 && chown -R appuser:appuser /app /config

# Install dependencies first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/requirements.txt

# Copy only what is required to run the service
COPY app.py /app/app.py

EXPOSE 5000

USER appuser

CMD ["python", "app.py"]
