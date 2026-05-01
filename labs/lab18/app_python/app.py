"""DevOps Info Service — Lab 1 baseline used for Lab 18 Nix comparison."""
from __future__ import annotations

import os
import platform
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)
_START = datetime.now(timezone.utc)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def _uptime() -> tuple[int, str]:
    delta = datetime.now(timezone.utc) - _START
    seconds = int(delta.total_seconds())
    hours, rem = divmod(seconds, 3600)
    minutes, _ = divmod(rem, 60)
    return seconds, f"{hours} hours, {minutes} minutes"


@app.route("/")
def index():
    up_s, up_h = _uptime()
    return jsonify(
        {
            "service": {
                "name": "devops-info-service",
                "version": "1.0.0",
                "description": "DevOps course info service",
                "framework": "Flask",
            },
            "system": {
                "hostname": socket.gethostname(),
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "cpu_count": os.cpu_count() or 0,
                "python_version": platform.python_version(),
            },
            "runtime": {
                "uptime_seconds": up_s,
                "uptime_human": up_h,
                "current_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "timezone": "UTC",
            },
            "request": {
                "client_ip": request.remote_addr or "",
                "user_agent": request.headers.get("User-Agent", ""),
                "method": request.method,
                "path": request.path,
            },
            "endpoints": [
                {"path": "/", "method": "GET", "description": "Service information"},
                {"path": "/health", "method": "GET", "description": "Health check"},
            ],
        }
    )


@app.route("/health")
def health():
    up_s, _ = _uptime()
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "uptime_seconds": up_s,
        }
    )


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
