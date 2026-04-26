# Use specific version of Python slim image for smaller base
FROM python:3.13-slim

# Set environment variables
#   PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files
#   PYTHONUNBUFFERED: Ensures logs are immediately flushed to stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create app directory with proper ownership
WORKDIR /app

# Install system dependencies (if any) and create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy only requirements file first for better layer caching
# This layer will only be rebuilt when requirements.txt changes
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# Copy after installing dependencies to maximize layer caching
COPY app.py .

# Create writable runtime directories and change ownership to non-root user
RUN mkdir -p /data /config && chown -R appuser:appuser /app /data /config

# Switch to non-root user for security
USER appuser

# Expose port (documentation only, actual mapping done at runtime)
EXPOSE 8000

# Set default environment variables
ENV HOST=0.0.0.0 \
    PORT=8000 \
    DEBUG=False \
    VISITS_FILE=/data/visits \
    CONFIG_FILE=/config/config.json

# Health check to verify container is running
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "app.py"]
