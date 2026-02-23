# DevOps Info Service - Production Dockerfile
# Using multi-stage approach for optimized image

# Stage 1: Base image with Python
FROM python:3.13-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Stage 2: Build dependencies
FROM base AS builder

WORKDIR /build

# Copy only requirements first (layer caching optimization)
COPY requirements.txt .

# Install dependencies to a specific directory
RUN pip install --target=/build/deps -r requirements.txt

# Stage 3: Final production image
FROM base AS production

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /build/deps /usr/local/lib/python3.13/site-packages/

# Copy application code
COPY --chown=appuser:appgroup app.py .

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 5000

# Set default environment variables
ENV HOST=0.0.0.0 \
    PORT=5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run the application
CMD ["python", "app.py"]
