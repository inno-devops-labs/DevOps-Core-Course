
FROM python:3.13-slim

WORKDIR /app

RUN groupadd -r appuser -g 1000 && \
    useradd -r -u 1000 -g appuser appuser

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=false

CMD ["python", "app.py"]