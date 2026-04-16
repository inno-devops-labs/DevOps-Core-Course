FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd -r appgroup && useradd -r -g appgroup appuser

RUN mkdir -p /data && chown appuser:appgroup /data

COPY app.py .

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

ENV PORT=5000

CMD ["python", "app.py"]
