FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install deps first
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY app.py .
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Run app finally
CMD ["python", "app.py"]
