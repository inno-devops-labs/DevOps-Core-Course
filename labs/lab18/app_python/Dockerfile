FROM python:3.13-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy requirements first (better layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["python", "app.py"]
