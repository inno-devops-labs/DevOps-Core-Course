FROM python:3.12-slim

RUN useradd --create-home appuser

WORKDIR /app

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    --default-timeout=120 \
    --retries 10 \
    -r requirements.txt

COPY app.py .

RUN mkdir -p /data /config && chown -R appuser:appuser /app /data /config

USER appuser

EXPOSE 5000
CMD ["python", "app.py"]
