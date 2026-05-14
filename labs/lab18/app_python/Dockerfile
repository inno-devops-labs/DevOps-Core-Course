FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN useradd -m dockeruser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R dockeruser:dockeruser /app
RUN mkdir -p /data && chown -R dockeruser:dockeruser /data
USER dockeruser

EXPOSE 5000

CMD ["python", "app.py"]
