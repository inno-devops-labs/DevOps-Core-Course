FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_NAME=devops-info-service \
    APP_ENV=container \
    PORT=3000 \
    VISITS_FILE_PATH=/data/visits \
    APP_CONFIG_PATH=/config/config.json

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --system app && adduser --system --ingroup app app

COPY app.py ./
RUN mkdir -p /app /data /config && chown -R app:app /app /data /config

USER app

EXPOSE 3000

CMD ["python", "app.py"]
