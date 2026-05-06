from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    moscow_time = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")
    return f"""
    <html>
        <head>
            <title>Moscow Time</title>
        </head>
        <body>
            <h1>Current time in Moscow</h1>
            <p>{moscow_time}</p>
            <p>Refresh the page to update the time.</p>
        </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
