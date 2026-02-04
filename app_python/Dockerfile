# DevOps Info Service - Python Container
# Production-ready Dockerfile with best practices

# Use specific Python slim image for smaller size and security updates
FROM python:3.13-slim

# Set environment variables
# Prevents Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Create non-root user for security
# Running as non-root prevents container breakout attacks
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid 1000 --create-home appuser

# Copy only requirements first (layer caching optimization)
# This layer is cached unless requirements.txt changes
COPY requirements.txt .

# Install dependencies
# --no-cache-dir reduces image size by not caching pip packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (after dependencies for better caching)
# This layer rebuilds when app code changes, but dependencies stay cached
COPY app.py .

# Change ownership of app files to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Document the port the app uses
EXPOSE 8000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
