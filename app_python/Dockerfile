FROM python:3.14-slim
RUN useradd --shell /bin/sh appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
USER appuser
CMD ["python", "-m", "src.app"]
