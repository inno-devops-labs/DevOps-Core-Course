# Stage: Production Image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies required at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
# This layer is only rebuilt if requirements.txt changes
COPY requirements.txt .

# Install Python dependencies
# Using --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code after dependencies
# This layer is rebuilt more frequently, so keeping it last improves caching
COPY app.py .

# Create a non-root user for security
# This is critical - running as root in containers is a security risk
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Document which port the application uses
EXPOSE 8080

# Health check to verify container is healthy
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]