import logging
import json
import time
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# ──────────────────────────────────────────────
# JSON Logger (Lab 7)
# ──────────────────────────────────────────────
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "method"):
            log_record["method"] = record.method
        if hasattr(record, "path"):
            log_record["path"] = record.path
        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code
        if hasattr(record, "client_ip"):
            log_record["client_ip"] = record.client_ip
        if hasattr(record, "duration_ms"):
            log_record["duration_ms"] = record.duration_ms
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("devops-python")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

# ──────────────────────────────────────────────
# Prometheus Metrics (Task 1)
# ──────────────────────────────────────────────

http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently being processed'
)

endpoint_calls_total = Counter(
    'devops_info_endpoint_calls_total',
    'Total calls per endpoint',
    ['endpoint']
)

@app.before_request
def before_request():
    request.start_time = time.time()
    http_requests_in_progress.inc()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    duration_ms = round(duration * 1000, 2)

    endpoint = request.path
    if endpoint not in ['/', '/health', '/metrics', '/error']:
        endpoint = '/other'

    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(response.status_code)
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)

    http_requests_in_progress.dec()

    # JSON лог (Lab 7)
    logger.info(
        "HTTP request",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "client_ip": request.remote_addr,
            "duration_ms": duration_ms,
        },
    )
    return response

# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route('/')
def index():
    endpoint_calls_total.labels(endpoint='/').inc()
    return jsonify({"status": "ok", "message": "Hello from DevOps Python App!"})

@app.route('/health')
def health():
    endpoint_calls_total.labels(endpoint='/health').inc()
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route('/error')
def error():
    endpoint_calls_total.labels(endpoint='/error').inc()
    try:
        raise ValueError("This is a test error for logging demonstration")
    except ValueError as e:
        logger.error("Unhandled error occurred", exc_info=True, extra={
            "method": request.method,
            "path": request.path,
            "client_ip": request.remote_addr,
        })
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    logger.info("Application starting up", extra={"port": 8000})
    app.run(host="0.0.0.0", port=8000)