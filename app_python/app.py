from flask import Flask, render_template
from utils.time_util import get_current_time_in_moscow
from os import environ

app = Flask(__name__)

HOST = environ.get("HOST", "0.0.0.0")
PORT = int(environ.get("PORT", "8080"))


@app.route("/")
def home():
    current_time = get_current_time_in_moscow()
    return render_template("index.html", current_time=current_time)


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=False)
