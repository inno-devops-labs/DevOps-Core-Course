FROM python:3.13-slim AS runtime

WORKDIR /app

COPY requirements.txt .

# Use --trusted-host for corporate networks with SSL inspection
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd -m appuser
RUN mkdir -p /data /config && chown -R appuser:appuser /app /data /config

COPY app.py .
COPY README.md ./README.md

USER appuser

# Expose application port
EXPOSE 5001

# Default strart command
CMD ["python", "app.py"]
