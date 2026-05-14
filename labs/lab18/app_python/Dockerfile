FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY docs ./docs

RUN mkdir -p /data && chown appuser:appgroup /data

USER appuser

EXPOSE 5000

CMD ["python", "app.py"]