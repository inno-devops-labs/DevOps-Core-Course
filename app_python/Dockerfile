FROM python:3.13-slim AS runtime

RUN apt-get update && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system appuser && useradd --system --create-home --gid appuser appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app.py .

USER appuser

EXPOSE 5000

ENV HOST=0.0.0.0 \
    PORT=5000 \
    DEBUG=False

CMD ["python", "app.py"]

