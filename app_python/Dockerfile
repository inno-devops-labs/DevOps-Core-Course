FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser /app

USER appuser

EXPOSE 5000

ENV HOST=0.0.0.0 PORT=5000

CMD ["python", "-u", "app.py"]