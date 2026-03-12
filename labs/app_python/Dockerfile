FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
COPY pip-packages/ /tmp/pip-packages/
RUN pip install --no-cache-dir --no-index --find-links=/tmp/pip-packages -r requirements.txt && rm -rf /tmp/pip-packages

COPY app.py .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "app:app"]
