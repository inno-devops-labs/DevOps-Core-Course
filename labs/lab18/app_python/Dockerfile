FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system app \
    && useradd --system --gid app --home /app --shell /usr/sbin/nologin app \
    && mkdir -p /data /config \
    && chown -R app:app /app /data /config

COPY --chown=app:app requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app app.py ./

USER app

EXPOSE 5000

CMD ["python", "app.py"]
