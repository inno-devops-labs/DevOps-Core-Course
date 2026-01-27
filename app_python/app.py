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

# Initialize Flask app
app = Flask(__name__)

# Configuration from environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time for uptime calculation
START_TIME = datetime.now(timezone.utc)


def get_system_info():
    """Collect system information."""
    try:
        return {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'cpu_count': os.cpu_count(),
            'python_version': platform.python_version()
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {}


def get_uptime():
    """Calculate application uptime since start."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    # Format human-readable uptime
    if hours > 0:
        human = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    elif minutes > 0:
        human = f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        human = f"{seconds} second{'s' if seconds != 1 else ''}"

    return {
        'seconds': seconds,
        'human': human
    }


def get_request_info():
    """Extract current request information."""
    return {
        'client_ip': request.remote_addr or 'unknown',
        'user_agent': request.headers.get('User-Agent', 'unknown'),
        'method': request.method,
        'path': request.path
    }


@app.route('/')
def index():
    """Main endpoint providing comprehensive service and system information."""
    logger.info(
        f'Request: {request.method} {request.path} from {request.remote_addr}')

    uptime = get_uptime()

    response_data = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask'
        },
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC'
        },
        'request': get_request_info(),
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
            }
        ]
    }

    return jsonify(response_data)


@app.route('/health')
def health():
    """Health check endpoint for monitoring and orchestration tools."""
    logger.debug(f'Health check from {request.remote_addr}')

    uptime = get_uptime()

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime['seconds']
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with JSON response."""
    logger.warning(f'404 error: {request.path}')
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist',
        'path': request.path
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with JSON response."""
    logger.error(f'500 error: {error}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    logger.info(f'Starting DevOps Info Service...')
    logger.info(f'Host: {HOST}, Port: {PORT}, Debug: {DEBUG}')
    logger.info(f'Visit: http://{HOST}:{PORT}/')

    app.run(host=HOST, port=PORT, debug=DEBUG)
