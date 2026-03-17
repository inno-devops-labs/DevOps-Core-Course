# 1. Base image (specific version, slim)
FROM python:3.11-slim

# 2. Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# 3. Create non-root user
RUN useradd --create-home appuser

# 4. Set working directory
WORKDIR /app

# 5. Copy only requirements first (layer caching)
COPY requirements.txt .

# 6. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy application source code
COPY . .

# 8. Switch to non-root user
USER appuser

# 9. Expose application port
EXPOSE 8080

# 10. Run application
CMD ["python", "app.py"]
