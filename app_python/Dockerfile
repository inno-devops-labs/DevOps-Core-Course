# syntax=docker/dockerfile:1.7
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies first to leverage layer caching
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Create dedicated non-root user
RUN addgroup --system app \
    && adduser --system --ingroup app app

# Copy only the application code needed at runtime
COPY --chown=app:app app.py ./

USER app

EXPOSE 8080

CMD ["python", "app.py"]
