"""
Flask application for displaying the current time in Moscow
"""

import logging
import os
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify
import pytz


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")
_visits_lock = threading.Lock()


def _read_visits():
    try:
        with open(VISITS_FILE, "r", encoding="utf-8") as handle:
            return int(handle.read().strip() or "0")
    except FileNotFoundError:
        return 0
    except ValueError:
        return 0


def _write_visits(value):
    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    tmp_path = f"{VISITS_FILE}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        handle.write(str(value))
    os.replace(tmp_path, VISITS_FILE)


def _increment_visits():
    with _visits_lock:
        current = _read_visits()
        current += 1
        _write_visits(current)
        return current


def get_moscow_time():
    """
    Current MSK Time
    """
    moscow_tz = pytz.timezone("Europe/Moscow")
    return datetime.now(moscow_tz).strftime("%H:%M:%S")


@app.route("/ct")
def get_time():
    """
    Used to get MSK time and use it in script.js file
    """
    return jsonify({"ct": get_moscow_time()})


@app.route("/")
def index():
    """
    Displays the current time in Moscow
    """
    logging.info("Main page with timezone was loaded")
    moscow_tz = pytz.timezone("Europe/Moscow")
    current_time = datetime.now(moscow_tz).strftime("%H:%M:%S")
    _increment_visits()

    return render_template("index.html", time=current_time)


@app.route("/visits")
def visits():
    """
    Returns visits count.
    """
    with _visits_lock:
        return jsonify({"visits": _read_visits()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
