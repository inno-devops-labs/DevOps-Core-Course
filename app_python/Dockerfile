FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /bin/sh --uid 10001 appuser && \
    mkdir -p /data && \
    chown 10001:10001 /data
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY src ./src
EXPOSE 5000
USER appuser
CMD ["python", "app.py"]
