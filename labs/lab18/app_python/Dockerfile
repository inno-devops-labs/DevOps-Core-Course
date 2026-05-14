FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app

RUN groupadd -r mariaapp && useradd -r -g mariaapp mariaapp

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY *.py .
COPY requirements.txt .

RUN chown -R mariaapp:mariaapp /app
USER mariaapp

EXPOSE 5000

ENV HOST=0.0.0.0 PORT=5000

CMD uvicorn app:app --host 0.0.0.0 --port 5000