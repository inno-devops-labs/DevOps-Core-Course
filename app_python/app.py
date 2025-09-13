from flask import Flask, render_template
from utils.time_util import get_current_time_in_moscow
from os import environ
import os

from prometheus_client import generate_latest, REGISTRY, Counter, Gauge

REQUEST_COUNTER = Counter(
    "app_http_requests_total",
    "Total HTTP Requests",
    ["method", "endpoint", "status"],
)

HEALTH_GAUGE = Gauge(
    "app_health_status", "Application Health Status (1=healthy, 0=unhealthy)"
)

VISITS_FILE = "visits"


def read_visits():
    """Retrieve the current visit count from the file."""

    if not os.path.exists(VISITS_FILE):
        return 0
    try:
        with open(VISITS_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except ValueError:
        return 0


def inc_visits():
    """Increment and update the visit count in the file."""

    count = read_visits() + 1
    with open(VISITS_FILE, "w", encoding="utf-8") as f:
        f.write(str(count))

    return count


app = Flask(__name__)

HOST = environ.get("HOST", "0.0.0.0")
PORT = int(environ.get("PORT", "8080"))


@app.route("/")
def home():
    inc_visits()

    current_time = get_current_time_in_moscow()
    return render_template("index.html", current_time=current_time)


@app.route("/visits")
def visits():
    return {"visits": read_visits()}, 200


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": "text/plain; version=0.0.4"}


@app.route("/health")
def health_check():
    HEALTH_GAUGE.set(1)
    return "OK", 200


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=False)
