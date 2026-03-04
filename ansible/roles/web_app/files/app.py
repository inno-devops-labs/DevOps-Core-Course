import json
import os
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


START_TIME = time.time()
APP_NAME = os.getenv("APP_NAME", "devops-app")
PORT = int(os.getenv("APP_PORT", "5000"))


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_GET(self):
        if self.path == "/health":
            self._send_json(
                200,
                {
                    "status": "healthy",
                    "uptime_seconds": int(time.time() - START_TIME),
                },
            )
            return

        if self.path == "/":
            self._send_json(
                200,
                {
                    "message": "Hello from Ansible deployed app",
                    "app_name": APP_NAME,
                    "hostname": socket.gethostname(),
                },
            )
            return

        self._send_json(404, {"error": "not found", "path": self.path})

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
