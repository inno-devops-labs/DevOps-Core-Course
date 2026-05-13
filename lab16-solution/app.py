from flask import Flask, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
request_count = Counter('lab16_app_requests_total', 'Total HTTP requests received')

@app.route('/')
def index():
    request_count.inc()
    return 'Lab16 app metrics working', 200

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
