FROM python:3.13-slim

RUN groupadd -r -g 1000 appuser && useradd -r -u 1000 -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

CMD ["python", "app.py"]
