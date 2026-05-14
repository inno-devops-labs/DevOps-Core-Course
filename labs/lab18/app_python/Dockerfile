FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN groupadd -g 1000 nonroot \ 
    && useradd -r --no-create-home -u 1000 -g nonroot nonroot

RUN mkdir -p /data && chown -R nonroot:nonroot /data && chmod 755 /data

USER nonroot

EXPOSE 5000/tcp

ENTRYPOINT ["python", "app.py"]
