import os
import socket
import platform
import logging
import fcntl
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY

# ========== CONFIGURATION ==========
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# ========== PROMETHEUS METRICS ==========
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

REQUESTS_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed'
)

# Application-specific metrics
ENDPOINT_CALLS = Counter(
    'devops_info_endpoint_calls',
    'Calls to specific endpoints',
    ['endpoint']
)

# ========== APPLICATION SETUP ==========
app = Flask(__name__)

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')
logHandler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO if not DEBUG else logging.DEBUG)

logger = logging.getLogger(__name__)

START_TIME = datetime.now(timezone.utc)

# ========== COUNTER FILE ==========
COUNTER_FILE = os.getenv('COUNTER_FILE', '/data/visits')
DATA_DIR = os.path.dirname(COUNTER_FILE)

def read_counter():
    """Read current visit count from file, return int."""
    if not os.path.exists(COUNTER_FILE):
        return 0
    try:
        with open(COUNTER_FILE, 'r') as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            data = f.read().strip()
            fcntl.flock(f, fcntl.LOCK_UN)
            return int(data) if data else 0
    except (ValueError, IOError):
        return 0

def write_counter(value):
    """Write visit count to file atomically."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    with open(COUNTER_FILE, 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(str(value))
        fcntl.flock(f, fcntl.LOCK_UN)

# ========== MIDDLEWARE FOR METRICS ==========
@app.before_request
def before_request():
    REQUESTS_IN_PROGRESS.inc()

@app.after_request
def after_request(response):
    REQUESTS_IN_PROGRESS.dec()
    duration = datetime.now(timezone.utc) - request._start_time
    REQUEST_DURATION.labels(method=request.method, endpoint=request.endpoint or request.path).observe(duration.total_seconds())
    REQUEST_COUNT.labels(method=request.method, endpoint=request.endpoint or request.path, status=response.status_code).inc()
    return response

@app.before_request
def start_timer():
    request._start_time = datetime.now(timezone.utc)

# ========== HELPER FUNCTIONS ==========
def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {'seconds': seconds, 'human': f"{hours} hours, {minutes} minutes"}

def get_system_info():
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.release(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count() or 1,
        'python_version': platform.python_version()
    }

def get_request_info():
    return {
        'client_ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'method': request.method,
        'path': request.path
    }

# ========== ROUTES ==========
@app.route('/')
def main_endpoint():
    # Increment visit counter
    count = read_counter() + 1
    write_counter(count)
    logger.info(f"Visit #{count} from {request.remote_addr}")
    ENDPOINT_CALLS.labels(endpoint='/').inc()

    response = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask'
        },
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': get_uptime()['seconds'],
            'uptime_human': get_uptime()['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC'
        },
        'request': get_request_info(),
        'endpoints': [
            {'path': '/', 'method': 'GET', 'description': 'Service information'},
            {'path': '/health', 'method': 'GET', 'description': 'Health check'},
            {'path': '/visits', 'method': 'GET', 'description': 'Visit counter'},
            {'path': '/metrics', 'method': 'GET', 'description': 'Prometheus metrics'}
        ]
    }
    return jsonify(response)

@app.route('/health')
def health_check():
    logger.debug("Health check requested")
    response = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }
    return jsonify(response), 200

@app.route('/visits')
def visits():
    count = read_counter()
    return jsonify({'visits': count})

@app.route('/metrics')
def metrics():
    return generate_latest(REGISTRY), 200, {'Content-Type': 'text/plain; version=0.0.4'}

# ========== ERROR HANDLERS ==========
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist',
        'available_endpoints': ['/', '/health', '/visits', '/metrics']
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

# ========== APPLICATION ENTRY POINT ==========
if __name__ == '__main__':
    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
