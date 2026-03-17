FROM python:3.13-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1         PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd -m -u 10001 appuser

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only application source (not docs/tests/etc)
COPY app.py .

# Ensure ownership, then drop privileges
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
