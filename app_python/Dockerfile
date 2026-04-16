FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user and group
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --create-home --home-dir /home/appuser --shell /bin/bash appuser \
    && mkdir -p /app /data \
    && chown -R appuser:appgroup /app /data

WORKDIR /app

# Install Python dependencies first to leverage layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the application code
COPY app.py ./

# Ensure runtime directories stay writable for the non-root user
RUN chown -R appuser:appgroup /app /data
USER appuser

# Document the port the app uses
EXPOSE 5002

# Start the application
CMD ["python", "app.py"]
