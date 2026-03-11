"""
DevOps Info Service
Main application module
"""
import json
import os
import socket
import platform
import logging
import sys
from datetime import datetime, timezone
from flask import Flask, jsonify, request


def format_timestamp(timestamp: datetime | None = None) -> str:
    """Return a UTC timestamp in ISO-8601 format."""
    value = timestamp or datetime.now(timezone.utc)
    return value.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for log aggregation systems."""

    default_attrs = {
        'args',
        'asctime',
        'created',
        'exc_info',
        'exc_text',
        'filename',
        'funcName',
        'levelname',
        'levelno',
        'lineno',
        'module',
        'msecs',
        'message',
        'msg',
        'name',
        'pathname',
        'process',
        'processName',
        'relativeCreated',
        'stack_info',
        'taskName',
        'thread',
        'threadName',
    }

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': format_timestamp(
                datetime.fromtimestamp(record.created, tz=timezone.utc),
            ),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key in self.default_attrs:
                continue
            payload[key] = value

        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> logging.Logger:
    """Configure application-wide JSON logging to stdout."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(stream_handler)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    return logging.getLogger('devops-info-service')


logger = configure_logging()

app = Flask(__name__)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time
START_TIME = datetime.now(timezone.utc)


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    human = (
        f"{hours} hour{'s' if hours != 1 else ''}, "
        f"{minutes} minute{'s' if minutes != 1 else ''}"
    )
    return {'seconds': seconds, 'human': human}


def get_system_info():
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.platform(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count() or 0,
        'python_version': platform.python_version()
    }


def get_service_info():
    """Get service metadata."""
    return {
        'name': 'devops-info-service',
        'version': '1.0.0',
        'description': 'DevOps course info service',
        'framework': 'Flask'
    }


def get_runtime_info():
    """Get runtime information."""
    uptime = get_uptime()
    current_time = (
        datetime.now(timezone.utc)
        .isoformat()
        .replace('+00:00', '.000Z')
    )
    return {
        'uptime_seconds': uptime['seconds'],
        'uptime_human': uptime['human'],
        'current_time': current_time,
        'timezone': 'UTC',
    }


def get_request_info():
    """Get current request information."""
    return {
        'client_ip': get_client_ip(),
        'user_agent': request.headers.get('User-Agent', 'unknown'),
        'method': request.method,
        'path': request.path,
    }


def get_client_ip() -> str:
    """Extract client IP address with proxy awareness."""
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()

    return request.remote_addr or 'unknown'


@app.before_request
def log_request_started():
    """Log incoming HTTP requests before handlers execute."""
    request.start_time = datetime.now(timezone.utc)
    logger.info(
        'request_started',
        extra={
            'method': request.method,
            'path': request.path,
            'client_ip': get_client_ip(),
            'user_agent': request.headers.get('User-Agent', 'unknown'),
        },
    )


@app.after_request
def log_request_completed(response):
    """Log request completion status and execution time."""
    start_time = getattr(request, 'start_time', datetime.now(timezone.utc))
    duration_ms = int(
        (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
    )

    level = logging.INFO
    if response.status_code >= 500:
        level = logging.ERROR
    elif response.status_code >= 400:
        level = logging.WARNING

    logger.log(
        level,
        'request_completed',
        extra={
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'client_ip': get_client_ip(),
            'duration_ms': duration_ms,
        },
    )
    return response


@app.route('/')
def index():
    """Main endpoint - service and system information."""
    response = {
        'service': get_service_info(),
        'system': get_system_info(),
        'runtime': get_runtime_info(),
        'request': get_request_info(),
        'endpoints': [
            {
                'path': '/',
                'method': 'GET',
                'description': 'Service information',
            },
            {
                'path': '/health',
                'method': 'GET',
                'description': 'Health check',
            },
        ],
    }

    return jsonify(response)


@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    uptime = get_uptime()
    timestamp = format_timestamp()
    return jsonify(
        {
            'status': 'healthy',
            'timestamp': timestamp,
            'uptime_seconds': uptime['seconds'],
        },
    )


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning(
        'not_found',
        extra={
            'method': request.method,
            'path': request.path,
            'status_code': 404,
            'client_ip': get_client_ip(),
        },
    )
    return jsonify(
        {'error': 'Not Found', 'message': 'Endpoint does not exist'},
    ), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.exception(
        'internal_server_error',
        extra={
            'method': request.method,
            'path': request.path,
            'status_code': 500,
            'client_ip': get_client_ip(),
        },
    )
    return jsonify(
        {
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
        },
    ), 500

@app.route('/boom')
def boom():
    raise RuntimeError("synthetic lab error")


if __name__ == '__main__':
    logger.info(
        'application_starting',
        extra={
            'host': HOST,
            'port': PORT,
            'debug': DEBUG,
            'started_at': format_timestamp(START_TIME),
        },
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)
