FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=80

RUN addgroup --system app \
    && adduser --system --ingroup app app

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data && chown -R app:app /app /data

USER app

EXPOSE $APP_PORT

ENTRYPOINT ["sh", "-c"]
CMD ["python -m uvicorn app:app --host $APP_HOST --port $APP_PORT"]