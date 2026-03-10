import json
import logging
import os
import socket
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer


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


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_GET(self):
        client_ip = self.client_address[0]

        logger.info(
            "Incoming request",
            extra={"method": "GET", "path": self.path, "client_ip": client_ip},
        )

        try:
            if self.path == "/health":
                payload = {
                    "status": "healthy",
                    "uptime_seconds": int(time.time() - START_TIME),
                }
                self._send_json(200, payload)
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
                payload = {
                    "message": "Hello from DevOps monitoring lab",
                    "app_name": APP_NAME,
                    "hostname": socket.gethostname(),
                }
                self._send_json(200, payload)
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

            self._send_json(404, {"error": "not found", "path": self.path})
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
