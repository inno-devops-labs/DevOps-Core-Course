# Stage 1: Builder for dependencies (optional optimization)
# FROM python:3.13-slim AS builder
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.13-slim

# Metadata
LABEL maintainer="Savva Ponomarev <s.ponomarev@innopolis.university>"
LABEL description="DevOps Info Service - FastAPI System Monitoring"
LABEL version="1.0.0"

# Create non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/bash -m appuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8000
ENV HOST=0.0.0.0

# Set working directory
WORKDIR /app

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

# Command to run the application
CMD ["python", "app.py"]