FROM python:3.14.2-alpine3.23
# OPTIONAL: PORT {5000}, HOST {0.0.0.0}, DEBUG {false}

LABEL authors="xzsay"
RUN apk add --no-cache shadow  \
    && groupadd -g 122 -r appgroup \
    && useradd -u 122 -r -g appgroup -m appuser
WORKDIR /app

RUN pip install --upgrade pip>=26.0
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY . .
RUN mkdir -p /data /config \
    && chown -R appuser:appgroup /app /data /config
USER 122:122
ENTRYPOINT ["python", "app.py"]
EXPOSE 5000
