"""
DevOps Info Service
Main application module providing system and service information
"""
import os
import socket
import platform
import logging
import time
import tempfile
import threading
from datetime import datetime, timezone
from flask import Flask, jsonify, request, g
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

# ── JSON logging setup ────────────────────────────────────────────────────────
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()
        log_record["level"] = record.levelname
        log_record["service"] = "devops-info-service"

handler = logging.StreamHandler()
handler.setFormatter(CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s"))
logging.root.setLevel(logging.INFO)
logging.root.handlers = [handler]
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)

# Application-specific metrics
endpoint_calls_total = Counter(
    "devops_info_endpoint_calls_total",
    "Number of endpoint calls",
    ["endpoint"],
)

system_info_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "System information collection duration in seconds",
)


def normalize_endpoint(req):
    """Return low-cardinality route label for Prometheus metrics."""
    if req.url_rule and req.url_rule.rule:
        return req.url_rule.rule
    if req.path in ["/", "/health", "/metrics", "/visits"]:
        return req.path
    return "unknown"

# ── Request / response logging hooks ─────────────────────────────────────────
@app.before_request
def log_request():
    g.start_time = datetime.now(timezone.utc)
    g.metrics_start_time = time.perf_counter()
    g.metrics_endpoint = normalize_endpoint(request)
    g.metrics_gauge = http_requests_in_progress.labels(
        method=request.method,
        endpoint=g.metrics_endpoint,
    )
    g.metrics_gauge.inc()
    logger.info("http_request", extra={
        "method": request.method,
        "path": request.path,
        "client_ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", "unknown"),
    })

@app.after_request
def log_response(response):
    duration_ms = None
    if hasattr(g, "start_time"):
        delta = datetime.now(timezone.utc) - g.start_time
        duration_ms = round(delta.total_seconds() * 1000, 2)

    endpoint = getattr(g, "metrics_endpoint", normalize_endpoint(request))
    status_code = str(response.status_code)

    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=status_code,
    ).inc()

    if hasattr(g, "metrics_start_time"):
        duration_seconds = time.perf_counter() - g.metrics_start_time
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code,
        ).observe(duration_seconds)

    if hasattr(g, "metrics_gauge"):
        g.metrics_gauge.dec()

    endpoint_calls_total.labels(endpoint=endpoint).inc()

    logger.info("http_response", extra={
        "method": request.method,
        "path": request.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
    })
    return response

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
VISITS_FILE = os.getenv('VISITS_FILE', '/data/visits')
VISITS_LOCK = threading.Lock()

# Application start time
START_TIME = datetime.now(timezone.utc)

# Service metadata
SERVICE_INFO = {
    'name': 'devops-info-service',
    'version': '1.0.0',
    'description': 'DevOps course info service',
    'framework': 'Flask'
}


def read_visits_count():
    """
    Read visits counter from a file.

    Returns:
        int: current visits count
    """
    try:
        with open(VISITS_FILE, 'r', encoding='utf-8') as f:
            return int(f.read().strip() or "0")
    except FileNotFoundError:
        return 0
    except (ValueError, OSError) as exc:
        logger.warning("visits_read_failed", extra={"error": str(exc)})
        return 0


def write_visits_count(count):
    """
    Persist visits counter to a file using atomic replace.

    Args:
        count: current visits count
    """
    visits_dir = os.path.dirname(VISITS_FILE) or "."
    os.makedirs(visits_dir, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=visits_dir, prefix="visits-", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(str(count))
        os.replace(temp_path, VISITS_FILE)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def increment_visits_count():
    """
    Increment and persist visits counter with thread-level locking.

    Returns:
        int: updated visits count
    """
    with VISITS_LOCK:
        new_count = read_visits_count() + 1
        write_visits_count(new_count)
        return new_count


def get_system_info():
    """
    Collect system information.
    
    Returns:
        dict: System information including hostname, platform, architecture, etc.
    """
    with system_info_collection_seconds.time():
        return {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'platform_version': platform.release(),
            'architecture': platform.machine(),
            'cpu_count': os.cpu_count(),
            'python_version': platform.python_version()
        }


def get_uptime():
    """
    Calculate application uptime.
    
    Returns:
        dict: Uptime in seconds and human-readable format
    """
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


def get_request_info(req):
    """
    Extract request information.
    
    Args:
        req: Flask request object
        
    Returns:
        dict: Request information including client IP, user agent, etc.
    """
    return {
        'client_ip': req.remote_addr,
        'user_agent': req.headers.get('User-Agent', 'Unknown'),
        'method': req.method,
        'path': req.path
    }


@app.route('/')
def index():
    """
    Main endpoint - service and system information.
    
    Returns:
        JSON response with comprehensive service and system details
    """
    logger.debug(f'Request: {request.method} {request.path}')
    
    uptime_data = get_uptime()
    
    visits_count = increment_visits_count()

    response = {
        'service': SERVICE_INFO,
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': uptime_data['seconds'],
            'uptime_human': uptime_data['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC'
        },
        'request': get_request_info(request),
        'visits': {
            'count': visits_count,
            'file': VISITS_FILE
        },
        'endpoints': [
            {
                'path': '/',
                'method': 'GET',
                'description': 'Service information'
            },
            {
                'path': '/health',
                'method': 'GET',
                'description': 'Health check'
            },
            {
                'path': '/metrics',
                'method': 'GET',
                'description': 'Prometheus metrics'
            },
            {
                'path': '/visits',
                'method': 'GET',
                'description': 'Current visits counter'
            }
        ]
    }
    
    return jsonify(response)


@app.route('/health')
def health():
    """
    Health check endpoint for monitoring and Kubernetes probes.
    
    Returns:
        JSON response with health status and uptime
    """
    logger.debug('Health check requested')
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }), 200


@app.route('/metrics')
def metrics():
    """Prometheus scrape endpoint."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route('/visits')
def visits():
    """
    Current visits counter endpoint.

    Returns:
        JSON response with persisted visits count
    """
    return jsonify({
        'visits': read_visits_count(),
        'file': VISITS_FILE,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error("internal_server_error", extra={"error": str(error)})
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    logger.info("app_startup", extra={
        "host": HOST,
        "port": PORT,
        "debug": DEBUG,
        "started_at": START_TIME.isoformat(),
    })
    app.run(host=HOST, port=PORT, debug=DEBUG)
