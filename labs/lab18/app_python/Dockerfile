# Dockerfile for Python Application with Virtual Environment
FROM python:3.13-slim AS builder

# Installing system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Installing the working directory
WORKDIR /app

# Creating a virtual environment
RUN python -m venv /opt/venv

# Activating the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copying requirements file
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Final stage: Copying the virtual environment and application code
FROM python:3.13-slim

# Creating non-root user and group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Setting the working directory
WORKDIR /app

# Copying the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copying the application code
COPY . .

# Setting permissions for the application directory
RUN chown -R appuser:appgroup /app && chmod -R 755 /app

# Switching to non-root user
USER appuser

# Setting the PATH to include the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Opening the port for the application
EXPOSE 5000

# Setting environment variables
ENV HOST=0.0.0.0
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

# Running the application
CMD ["python", "app.py"]
