# syntax=docker/dockerfile:1

FROM python:3.13.1-slim AS runtime

# Prevent Python from writing .pyc files and ensure logs are unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create a dedicated, non-root user
RUN groupadd --system app && useradd --system --gid app --uid 10001 --create-home app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the application code (no venv/tests/docs)
COPY --chown=app:app app.py .

EXPOSE 5000

USER app

# Flask app binds to 0.0.0.0 by default in this project (HOST env)
ENV HOST=0.0.0.0 \
    PORT=5000

CMD ["python", "app.py"]
