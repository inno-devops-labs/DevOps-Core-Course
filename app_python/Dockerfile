FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Non-root user setup
RUN useradd --create-home appuser

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

#Swithh to non-root user
USER appuser

EXPOSE 8000

CMD ["python", "app.py"]