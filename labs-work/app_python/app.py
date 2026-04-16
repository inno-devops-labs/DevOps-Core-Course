import json
import logging
import os
import platform
import socket
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5173))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
DATA_DIR = os.getenv('DATA_DIR', '/data')
VISITS_FILE = os.path.join(DATA_DIR, 'visits')

START_TIME = datetime.now(timezone.utc)
_visits_lock = threading.Lock()


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'path'):
            log_entry['path'] = record.path
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'client_ip'):
            log_entry['client_ip'] = record.client_ip
        return json.dumps(log_entry)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.handlers = []
logging.root.addHandler(handler)
logging.root.setLevel(logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.handlers = []
werkzeug_logger.addHandler(handler)
werkzeug_logger.propagate = False


def _read_visits():
    try:
        with open(VISITS_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def _write_visits(count):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(VISITS_FILE, 'w') as f:
        f.write(str(count))


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


def get_system_info():
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.platform(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }


def get_service_info():
    return {
        'name': 'devops-info-service',
        'version': '1.0.0',
        'description': 'DevOps course info service',
        'framework': 'Flask'
    }


def get_request_info():
    return {
        'client_ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'method': request.method,
        'path': request.path
    }


def get_endpoints_list():
    return [
        {'path': '/', 'method': 'GET', 'description': 'Service information'},
        {'path': '/health', 'method': 'GET', 'description': 'Health check'},
        {'path': '/visits', 'method': 'GET', 'description': 'Visit counter'}
    ]


@app.after_request
def log_request(response):
    logger.info(
        "Request processed",
        extra={
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'client_ip': request.remote_addr,
        },
    )
    return response


@app.route('/')
def index():
    with _visits_lock:
        count = _read_visits() + 1
        _write_visits(count)

    uptime = get_uptime()

    response = {
        'service': get_service_info(),
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC'
        },
        'request': get_request_info(),
        'endpoints': get_endpoints_list(),
        'visits': count
    }

    return jsonify(response)


@app.route('/visits')
def visits():
    with _visits_lock:
        count = _read_visits()
    return jsonify({'visits': count})


@app.route('/health')
def health():
    logger.debug("Health check requested")

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    })


@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.path}")
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist',
        'path': request.path
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
