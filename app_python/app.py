from datetime import datetime

import pytz
from flask import Flask, render_template, jsonify

START_HOST = "0.0.0.0"
START_PORT = 5000
app = Flask(__name__)


def get_current_time() -> str:
    msk_tz = pytz.timezone("Europe/Moscow")
    current_time = datetime.now(msk_tz).strftime("%H:%M:%S")
    return current_time


@app.route("/")
def show_time():
    current_time = get_current_time()
    return render_template("index.html", time=current_time)


@app.route("/api/time/")
def get_time():
    current_time = get_current_time()
    return jsonify({"time": current_time})


if __name__ == "__main__":
    app.run(host=START_HOST, port=START_PORT)
