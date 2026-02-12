"""
DevOps Info Service
Main application module
"""
import os
import socket
import platform
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    client_ip = request.remote_addr or request.environ.get(
        'HTTP_X_FORWARDED_FOR',
        'unknown',
    )
    return {
        'client_ip': client_ip,
        'user_agent': request.headers.get('User-Agent', 'unknown'),
        'method': request.method,
        'path': request.path,
    }


@app.route('/')
def index():
    """Main endpoint - service and system information."""
    logger.info(
        'Request: %s %s from %s',
        request.method,
        request.path,
        request.remote_addr,
    )

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
    timestamp = (
        datetime.now(timezone.utc)
        .isoformat()
        .replace('+00:00', '.000Z')
    )
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
    return jsonify(
        {'error': 'Not Found', 'message': 'Endpoint does not exist'},
    ), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error('Internal server error: %s', error)
    return jsonify(
        {
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
        },
    ), 500


if __name__ == '__main__':
    logger.info('Application starting...')
    logger.info(f'Starting server on {HOST}:{PORT}')
    app.run(host=HOST, port=PORT, debug=DEBUG)
