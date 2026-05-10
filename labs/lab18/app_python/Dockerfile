# Use specific Python version - slim variant for smaller size
FROM python:3.12-slim

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy only requirements first for layer caching optimization
# If requirements don't change, Docker reuses this layer
COPY requirements.txt .

# Install dependencies as root (needed for pip install)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create data directory for visits persistence
RUN mkdir -p /data

# Change ownership to non-root user
RUN chown -R appuser:appuser /app /data

# Switch to non-root user
USER appuser

# Document which port the app uses
EXPOSE 8080

# Set default environment variables
ENV HOST=0.0.0.0 \
    PORT=8080 \
    DEBUG=False

# Run the application
CMD ["python", "app.py"]
