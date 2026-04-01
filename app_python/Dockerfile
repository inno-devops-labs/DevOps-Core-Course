# syntax=docker/dockerfile:1

FROM python:3.13.1-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --uid 10001 --create-home app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app app.py .

RUN mkdir -p /data && chown -R app:app /data

EXPOSE 5000

USER app

ENV HOST=0.0.0.0 \
    PORT=5000 \
    DATA_DIR=/data

CMD ["python", "app.py"]
