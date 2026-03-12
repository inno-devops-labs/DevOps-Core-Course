"""
DevOps Info Service
Main application module providing system information and health check.
"""

import json
import logging
import os
import platform
import socket
import sys
import time
from datetime import UTC, datetime

from flask import Flask, g, jsonify, request

app = Flask(__name__)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 3000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
SERVICE_NAME = 'devops-info-service'

# Application start time for uptime calculation
START_TIME = datetime.now(UTC)


class JSONFormatter(logging.Formatter):
    """Serialize log records to JSON for log aggregation systems."""

    def format(self, record):
        payload = {
            'timestamp': datetime.fromtimestamp(record.created, UTC).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }

        structured_data = getattr(record, 'structured_data', None)
        if isinstance(structured_data, dict):
            payload.update(
                {
                    key: value for key, value in structured_data.items()
                    if value is not None
                }
            )

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def configure_logging():
    """Configure the root logger to emit JSON logs to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(LOG_LEVEL)

    app.logger.handlers.clear()
    app.logger.propagate = True

    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers.clear()
    werkzeug_logger.propagate = True


def log_event(level, message, **fields):
    """Emit a structured application log entry."""
    logging.getLogger(SERVICE_NAME).log(
        level,
        message,
        extra={'structured_data': fields}
    )


configure_logging()


def get_system_info():
    """Collect comprehensive system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(UTC) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    hour_text = "hour" if hours == 1 else "hours"
    minute_text = "minute" if minutes == 1 else "minutes"

    return {
        'seconds': seconds,
        'human': f"{hours} {hour_text}, {minutes} {minute_text}"
    }


def get_runtime_info():
    """Get current runtime information."""
    uptime = get_uptime()
    return {
        'uptime_seconds': uptime['seconds'],
        'uptime_human': uptime['human'],
        'current_time': datetime.now(UTC).isoformat(),
        'timezone': 'UTC'
    }


def get_request_info(req):
    """Extract information from the current request."""
    return {
        'client_ip': req.remote_addr,
        'user_agent': req.headers.get('User-Agent', 'Unknown'),
        'method': req.method,
        'path': req.path
    }


def get_endpoints_list():
    """Return list of available endpoints."""
    return [
        {
            'path': '/',
            'method': 'GET',
            'description': 'Service and system information'
        },
        {
            'path': '/health',
            'method': 'GET',
            'description': 'Health check endpoint'
        }
    ]


@app.before_request
def before_request_logging():
    """Store request timing for structured access logs."""
    g.request_started_at = time.perf_counter()


@app.after_request
def after_request_logging(response):
    """Emit a structured access log for every request."""
    duration_ms = round(
        (time.perf_counter() - getattr(g, 'request_started_at', time.perf_counter()))
        * 1000,
        2
    )

    level = logging.INFO
    if response.status_code >= 500:
        level = logging.ERROR
    elif response.status_code >= 400:
        level = logging.WARNING

    log_event(
        level,
        'request.completed',
        service=SERVICE_NAME,
        method=request.method,
        path=request.path,
        status_code=response.status_code,
        client_ip=request.remote_addr,
        user_agent=request.headers.get('User-Agent', 'Unknown'),
        duration_ms=duration_ms
    )
    return response


@app.route('/')
def index():
    """
    Main endpoint - returns comprehensive service and system information.

    Returns:
        JSON response with service, system, runtime, and request information.
    """
    response = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask'
        },
        'system': get_system_info(),
        'runtime': get_runtime_info(),
        'request': get_request_info(request),
        'endpoints': get_endpoints_list()
    }

    return jsonify(response), 200


@app.route('/health')
def health():
    """
    Health check endpoint for monitoring and Kubernetes probes.

    Returns:
        JSON response with health status and uptime.
    """
    response = {
        'status': 'healthy',
        'timestamp': datetime.now(UTC).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }

    return jsonify(response), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist',
        'status_code': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    log_event(
        logging.ERROR,
        'request.failed',
        service=SERVICE_NAME,
        method=request.method,
        path=request.path,
        client_ip=request.remote_addr,
        error=str(error)
    )
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status_code': 500
    }), 500


if __name__ == '__main__':
    log_event(
        logging.INFO,
        'app.startup',
        service=SERVICE_NAME,
        host=HOST,
        port=PORT,
        debug=DEBUG,
        started_at=START_TIME.isoformat(),
        endpoints=['/', '/health']
    )

    app.run(host=HOST, port=PORT, debug=DEBUG)
