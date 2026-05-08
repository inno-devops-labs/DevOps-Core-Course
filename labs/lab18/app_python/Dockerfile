FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

RUN groupadd -g 10001 app && \
    useradd --no-log-init -m -u 10001 -g 10001 -s /usr/sbin/nologin app && \
    chown -R app:app /app

COPY --chown=app:app app.py /app/app.py

USER app

EXPOSE 5002

CMD ["python", "app.py"]