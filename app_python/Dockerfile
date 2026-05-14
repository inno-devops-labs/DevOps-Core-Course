# syntax=docker/dockerfile:1
FROM python:3.14-alpine

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV HOME=/home/appuser
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN apk upgrade -U \
    && addgroup -S appgroup \
    && adduser -S -D -h /home/appuser -s /sbin/nologin -G appgroup appuser \
    && mkdir -p /data \
    && chown -R appuser:appgroup /app /data /home/appuser

COPY pyproject.toml uv.lock gunicorn.conf.py ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY --chown=appuser:appgroup src ./src

ENV PORT=5000
ENV HOST="0.0.0.0"

USER appuser
CMD ["gunicorn", "--config", "/app/gunicorn.conf.py", "src.main:app"]
