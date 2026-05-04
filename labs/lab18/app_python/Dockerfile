FROM dockerhub.timeweb.cloud/library/python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN useradd --create-home appuser && \
    mkdir -p /app/data /app/config && \
    chown -R appuser:appuser /app

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

USER appuser

EXPOSE 8000

CMD ["python", "app.py"]