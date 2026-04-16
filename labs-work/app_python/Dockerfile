FROM python:3.13-slim

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY requirements.txt .

RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

COPY app.py .

RUN mkdir -p /data && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 5173

CMD ["python", "app.py"]
