from datetime import datetime

import pytz
from flask import Flask, render_template, jsonify
import os

START_HOST = "0.0.0.0"
START_PORT = 5000
app = Flask(__name__)

VISITS_FILE = "visits.txt"


class VisitsController:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.visits_counter = self._read_counter()

    def _read_counter(self) -> int:
        try:
            with open(self.file_path, "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def _write_counter(self) -> None:
        with open(self.file_path, "w") as f:
            f.write(str(self.visits_counter))

    def increment(self) -> int:
        self.visits_counter += 1
        self._write_counter()
        return self.visits_counter

    def get_counter(self) -> int:
        self.visits_counter = self._read_counter()
        return self.visits_counter


visits_controller = VisitsController(file_path=VISITS_FILE)


def get_current_time() -> str:
    visits_controller.increment()
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


@app.route("/visits")
def get_visits():
    return jsonify(visits_controller.get_counter())


if __name__ == "__main__":
    app.run(host=START_HOST, port=START_PORT)
