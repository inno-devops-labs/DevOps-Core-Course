# syntax=docker/dockerfile:1.7

############################
# Stage 1: build wheels
############################
FROM python:3.13-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
 && python -m pip wheel --wheel-dir /wheels -r requirements.txt


############################
# Stage 2: runtime
############################
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=5000 \
    DEBUG=FALSE

WORKDIR /app

RUN addgroup --system app \
 && adduser --system --ingroup app --home /home/app --shell /usr/sbin/nologin app

COPY --from=builder /wheels /wheels
COPY requirements.txt .

RUN python -m pip install --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

COPY app.py .

USER app

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health').read()" || exit 1

CMD ["python", "app.py"]
