FROM python:3.12-slim
WORKDIR /app_python
COPY requirements.txt .

# Installs newest packet versions(or reloads indices) without additional recomendations, 
# clears cache from installation, 
# creates non-root user, 
# and installs python requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser \
    && pip install --no-cache-dir -r requirements.txt

    COPY app.py .
#COPY templates/ templates/
# There are no /templates now...

EXPOSE 5000

USER appuser

CMD ["python", "app.py"]