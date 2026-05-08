FROM python:3.13-slim
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
COPY app.py .
USER appuser
EXPOSE 5001
CMD ["python", "app.py"]
