# Use specific, minimal Python base image
FROM python:3.13-slim

# Keep Python output unbuffered and avoid writing .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/app/.local/bin:${PATH}"

# Create a non-root user and group for running the app
RUN groupadd -r app && useradd -r -g app -m -d /home/app -s /sbin/nologin app

WORKDIR /home/app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy only the application code and set ownership to non-root user
COPY --chown=app:app app.py .

# Expose the port the application listens on
EXPOSE 5000

# Run as non-root user
USER app

# Start the application using uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
