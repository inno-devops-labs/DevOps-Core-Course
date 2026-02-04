FROM python:3.13-slim

WORKDIR /app

RUN groupadd -r appuser && \
    useradd -r -g appuser -s /bin/bash -u 1001 appuser

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5001

ENV HOST=0.0.0.0 \
    PORT=5001 \
    DEBUG=False

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/health')" || exit 1

CMD ["python", "app.py"]
