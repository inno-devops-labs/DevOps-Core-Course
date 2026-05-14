# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Stage 2: Final Image
FROM python:3.12-slim

# Create a non-root user and group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set working directory
WORKDIR /home/appuser

# Copy dependencies and application from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /app .

# Create writable data directory for persisted visits counter
RUN mkdir -p /data

# Change ownership of the directory
RUN chown -R appuser:appgroup /home/appuser /data

# Switch to the non-root user
USER appuser

# Expose the application port
EXPOSE 8080

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
