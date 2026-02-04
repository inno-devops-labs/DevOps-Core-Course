import logging
import os
import platform
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

START_TIME = datetime.now(timezone.utc)

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("devops-info-service")


def uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    return seconds


@app.route("/")
def index():
    return jsonify(
        service={"name": "devops-info-service", "framework": "Flask"},
        system={
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "python": platform.python_version(),
        },
        runtime={
            "uptime_seconds": uptime(),
            "time": datetime.now(timezone.utc).isoformat(),
        },
        request={
            "method": request.method,
            "path": request.path,
            "client_ip": request.remote_addr,
        },
    )


@app.route("/health")
def health():
    return jsonify(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=uptime(),
    )


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
