# Use specific Python version for reproducibility
FROM python:3.13-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements first for better layer caching
# This layer will be cached unless requirements.txt changes
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Persisted visit counter (Lab 12); writable when using a volume or emptyDir
RUN mkdir -p /data /config && chown -R appuser:appuser /app /data /config

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables with defaults
ENV HOST=0.0.0.0 \
    PORT=5000 \
    DEBUG=false

# Run the application
CMD ["python", "app.py"]
