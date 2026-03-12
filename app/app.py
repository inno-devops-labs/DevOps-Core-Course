import logging
import json
import time
from datetime import datetime, timezone
from flask import Flask, request, jsonify

app = Flask(__name__)


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


@app.before_request
def before_request():
    request.start_time = time.time()


@app.after_request
def after_request(response):
    duration_ms = round((time.time() - request.start_time) * 1000, 2)
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


@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "Hello from DevOps Python App!"})


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})


@app.route("/error")
def error():
    try:
        raise ValueError("This is a test error for logging demonstration")
    except ValueError as e:
        logger.error("Unhandled error occurred", exc_info=True, extra={
            "method": request.method,
            "path": request.path,
            "client_ip": request.remote_addr,
        })
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    logger.info("Application starting up", extra={"port": 8000})
    app.run(host="0.0.0.0", port=8000)