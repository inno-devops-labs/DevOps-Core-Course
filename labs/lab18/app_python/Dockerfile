FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system appuser && useradd --system --gid appuser --create-home appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

RUN mkdir -p /data && chown -R appuser:appuser /app /data
USER appuser

EXPOSE 8000

CMD ["python", "app.py"]
