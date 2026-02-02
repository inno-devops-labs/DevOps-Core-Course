FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Also we can use bitnami/python docker image which use non-root user by default
RUN groupadd -g 1000 nonroot \ 
    && useradd -r --no-create-home -u 1000 -g nonroot nonroot

USER nonroot

EXPOSE 5000/tcp

ENTRYPOINT ["python", "app.py"]
