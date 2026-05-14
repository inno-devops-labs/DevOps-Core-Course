FROM python:3.12-slim

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install flask python-json-logger

COPY . .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

ENV HOST=0.0.0.0
ENV PORT=5000
ENV DEBUG=False

CMD ["python", "app.py"]