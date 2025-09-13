from flask import Flask, render_template
from utils.time_util import get_current_time_in_moscow
from os import environ

from prometheus_client import generate_latest, REGISTRY, Counter, Gauge

REQUEST_COUNTER = Counter(
    "app_http_requests_total",
    "Total HTTP Requests",
    ["method", "endpoint", "status"],
)

HEALTH_GAUGE = Gauge(
    "app_health_status", "Application Health Status (1=healthy, 0=unhealthy)"
)

app = Flask(__name__)

HOST = environ.get("HOST", "0.0.0.0")
PORT = int(environ.get("PORT", "8080"))


@app.route("/")
def home():
    current_time = get_current_time_in_moscow()
    return render_template("index.html", current_time=current_time)


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": "text/plain; version=0.0.4"}


@app.route("/health")
def health_check():
    HEALTH_GAUGE.set(1)
    return "OK", 200


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=False)
