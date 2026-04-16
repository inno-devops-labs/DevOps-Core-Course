FROM python:3.13-slim

RUN groupadd --system appuser \
    && useradd --system --gid appuser --create-home appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN mkdir -p /data && chown -R appuser:appuser /data

USER appuser

EXPOSE 8000

CMD ["python", "app.py"]
