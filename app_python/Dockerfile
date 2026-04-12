# Use specific Python version for reproducibility
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
# -r creates a system user, -s /bin/bash sets shell, -u 1000 sets UID
RUN useradd -r -s /bin/bash -u 1000 appuser && \
    mkdir -p /data && \
    chown -R appuser:appuser /app /data

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install dependencies as root
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# This layer is rebuilt when application code changes
COPY app.py .

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables
ENV HOST=0.0.0.0 \
    PORT=5000 \
    PYTHONUNBUFFERED=1

# Health check to monitor container health
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

# Run the application
CMD ["python", "app.py"]
