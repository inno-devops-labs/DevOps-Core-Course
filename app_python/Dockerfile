FROM python:3.13-slim

ARG PORT=5000

WORKDIR /app/app_python

COPY requirements.txt .
COPY app.py .

RUN \ 
    pip install --no-cache-dir -r requirements.txt && \
    useradd --create-home --shell /usr/sbin/nologin appuser &&\
    chown -R appuser /app/app_python

USER appuser

EXPOSE ${PORT}

CMD [ "python", "app.py" ]