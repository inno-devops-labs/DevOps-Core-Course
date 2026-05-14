FROM python:3.13-slim

# restricted user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY requirements.txt .

# pip installation requires root
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# adduser now owns app
RUN mkdir -p /data && chown -R appuser:appuser /app /data

USER appuser

ENV VISITS_FILE=/data/visits

EXPOSE 5000

CMD ["python", "app.py"]
