# Stage 1: Build environment
FROM python:3.12-alpine AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime environment
FROM python:3.12-alpine

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
WORKDIR /home/appuser/app

# Copy only necessary files
COPY --from=builder /root/.local /home/appuser/.local
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Set environment variables and permissions
ENV PATH=/home/appuser/.local/bin:$PATH
RUN chown -R appuser:appuser /home/appuser
USER appuser

EXPOSE 5000
CMD ["python", "app.py"]