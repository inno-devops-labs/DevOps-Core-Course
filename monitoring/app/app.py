import json
import logging
import os
import socket
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from prometheus_client import Counter, Gauge, Histogram, generate_latest

# --------------- Prometheus metrics ---------------

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)

devops_info_endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "Endpoint calls by endpoint name",
    ["endpoint"],
)

devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information",
)

# --------------- JSON logging ---------------


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        if hasattr(record, "path"):
            log_entry["path"] = record.path
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "client_ip"):
            log_entry["client_ip"] = record.client_ip
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


logger = logging.getLogger("devops-app")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

START_TIME = time.time()
APP_NAME = os.getenv("APP_NAME", "devops-app")
PORT = int(os.getenv("APP_PORT", "8000"))
DATA_DIR = os.getenv("DATA_DIR", "/data")
VISITS_FILE = os.path.join(DATA_DIR, "visits")

_visits_lock = threading.Lock()


def _read_visits() -> int:
    try:
        return int(Path(VISITS_FILE).read_text().strip())
    except (FileNotFoundError, ValueError):
        return 0


def _write_visits(count: int) -> None:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    tmp = VISITS_FILE + ".tmp"
    Path(tmp).write_text(str(count))
    os.replace(tmp, VISITS_FILE)


def increment_visits() -> int:
    with _visits_lock:
        count = _read_visits() + 1
        _write_visits(count)
        return count


def get_visits() -> int:
    with _visits_lock:
        return _read_visits()


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_GET(self):
        start = time.time()
        http_requests_in_progress.inc()
        client_ip = self.client_address[0]

        logger.info(
            "Incoming request",
            extra={"method": "GET", "path": self.path, "client_ip": client_ip},
        )

        status_code = 200
        try:
            if self.path == "/metrics":
                data = generate_latest()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
                self.end_headers()
                self.wfile.write(data)
                return

            if self.path == "/health":
                payload = {
                    "status": "healthy",
                    "uptime_seconds": int(time.time() - START_TIME),
                }
                self._send_json(200, payload)
                devops_info_endpoint_calls.labels(endpoint="/health").inc()
                logger.info(
                    "Health check OK",
                    extra={
                        "method": "GET",
                        "path": self.path,
                        "status_code": 200,
                        "client_ip": client_ip,
                    },
                )
                return

            if self.path == "/":
                visits = increment_visits()
                with devops_info_system_collection_seconds.time():
                    payload = {
                        "message": "Hello from DevOps monitoring lab",
                        "app_name": APP_NAME,
                        "hostname": socket.gethostname(),
                        "visits": visits,
                    }
                self._send_json(200, payload)
                devops_info_endpoint_calls.labels(endpoint="/").inc()
                logger.info(
                    "Root endpoint served",
                    extra={
                        "method": "GET",
                        "path": self.path,
                        "status_code": 200,
                        "client_ip": client_ip,
                    },
                )
                return

            if self.path == "/visits":
                visits = get_visits()
                self._send_json(200, {"visits": visits})
                devops_info_endpoint_calls.labels(endpoint="/visits").inc()
                logger.info(
                    "Visits endpoint served",
                    extra={
                        "method": "GET",
                        "path": self.path,
                        "status_code": 200,
                        "client_ip": client_ip,
                    },
                )
                return

            status_code = 404
            self._send_json(404, {"error": "not found", "path": self.path})
            devops_info_endpoint_calls.labels(endpoint="/not_found").inc()
            logger.warning(
                "Route not found",
                extra={
                    "method": "GET",
                    "path": self.path,
                    "status_code": 404,
                    "client_ip": client_ip,
                },
            )

        except Exception:
            status_code = 500
            logger.exception(
                "Unhandled error",
                extra={
                    "method": "GET",
                    "path": self.path,
                    "status_code": 500,
                    "client_ip": client_ip,
                },
            )
            self._send_json(500, {"error": "internal server error"})

        finally:
            endpoint = self.path if self.path in ("/", "/health", "/visits") else "/other"
            duration = time.time() - start
            http_requests_total.labels(method="GET", endpoint=endpoint, status=str(status_code)).inc()
            http_request_duration_seconds.labels(method="GET", endpoint=endpoint).observe(duration)
            http_requests_in_progress.dec()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    logger.info(
        "Application starting",
        extra={
            "method": "STARTUP",
            "path": "/",
            "status_code": 0,
            "client_ip": "127.0.0.1",
        },
    )
    logger.info(
        f"Listening on port {PORT}, app_name={APP_NAME}",
        extra={
            "method": "STARTUP",
            "path": "/",
            "status_code": 0,
            "client_ip": "127.0.0.1",
        },
    )
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
