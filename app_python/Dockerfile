FROM python:3.12-alpine3.20

RUN addgroup -S appgroup \
    && adduser -D -h /home/appuser -G appgroup appuser

WORKDIR /home/appuser

COPY --chown=appuser:appgroup requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appgroup app.py .

EXPOSE 8080

USER appuser

CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
