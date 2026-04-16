FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY app_python/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY app_python/app.py .

RUN mkdir -p /data && chown -R appuser:appuser /data

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

ENV HOST=0.0.0.0 \
    PORT=5000 \
    DATA_DIR=/data

CMD ["python", "app.py"]

