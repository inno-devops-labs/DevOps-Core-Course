# Use specific Python version for reproducibility
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Healthcheck in docker-compose uses curl
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user with fixed UID/GID (matches typical fsGroup in Kubernetes)
RUN groupadd -g 1000 appuser && useradd -u 1000 -g appuser -m appuser

# Copy requirements first for better layer caching
# This layer will only rebuild if requirements.txt changes
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables with defaults
ENV HOST=0.0.0.0
ENV PORT=5000
ENV DEBUG=false

# Run the application
CMD ["python", "app.py"]
