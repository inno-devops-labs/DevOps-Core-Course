# Use a pinned Python base image version
FROM python:3.12-slim

# Best practice: disable .pyc, unbuffer logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user
RUN addgroup --system app && adduser --system --ingroup app app

# Set working directory
WORKDIR /app

# Copy only what is needed to install dependencies first (layer caching)
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the application code (not docs/tests)
COPY app.py /app/app.py

# Document the port (default app port)
EXPOSE 8005

# Switch to non-root user
USER app

# Start the application
CMD ["python", "app.py"]
