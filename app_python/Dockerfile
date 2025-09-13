# use python3.12 and alpine3.18 as the most stable versions for production
FROM python:3.12-alpine3.18 AS base

RUN addgroup -S appgroup
# use --uid to prevent user_id inconsistencies
RUN adduser --system --no-create-home --uid 1001 appuser -G appgroup

# cd to /app_python
WORKDIR /app_python

# copy all needed files
# specify appuser file ownership
COPY --chown=appuser:appgroup app.py requirements.txt ./
COPY --chown=appuser:appgroup templates/ ./templates/
COPY --chown=appuser:appgroup utils/ ./utils/

RUN touch /app_python/visits && chown appuser:appgroup /app_python/visits

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# login as appuser
USER appuser

EXPOSE 8080

# run the web-app
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
