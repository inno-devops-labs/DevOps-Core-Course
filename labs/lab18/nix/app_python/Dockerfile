FROM python:3.9-slim

RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
RUN mkdir -p /data && chown appuser:appuser /data
USER appuser

EXPOSE 5050

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:5050/health || exit 1

CMD ["python", "app.py"]
