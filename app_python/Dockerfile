# Build stage for Python dependencies (optional - can use for compilation if needed)
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=5000

# Create non-root user
RUN groupadd -r appuser && useradd -r -m -g appuser appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY app.py .

# Create directory for logs and set permissions
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# Command to run the application
# CMD bash
CMD ["python", "app.py"]
