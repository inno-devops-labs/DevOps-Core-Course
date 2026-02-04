FROM python:3.13-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user and group
RUN addgroup --system app && adduser --system --ingroup app app

# Set working directory
WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the application code needed at runtime
COPY app.py .

# Document the port the app listens on
EXPOSE 5000

# Switch to the non-root user
USER app

# Default environment (can be overridden at runtime)
ENV HOST=0.0.0.0 \
    PORT=5000

# Start the Flask application
CMD ["python", "app.py"]