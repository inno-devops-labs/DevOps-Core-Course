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

# Flask app initialization 
app = Flask(__name__)

# Configuration via environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application startup time
START_TIME = datetime.now(timezone.utc)

# Setting up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_system_info():
    """Collecting information about the system.

    Returns:
        dict: System configuration
    """
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.release(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count() or 0,
        'python_version': platform.python_version()
    }

def get_uptime():
    """Calculating the running time of the application.

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

@app.route('/')
def index():
    """The main endpoint - Information about the service and the system."""
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')

    # Forming a response
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
        'request': {
            'client_ip': client_ip,
            'user_agent': user_agent,
            'method': request.method,
            'path': request.path
        },
        'endpoints': [
            {'path': '/', 'method': 'GET', 'description': 'Service information'},
            {'path': '/health', 'method': 'GET', 'description': 'Health check'}
        ]
    }
    logger.info(f"Request: {request.method} {request.path} from {client_ip}")
    return jsonify(response)

@app.route('/health')
def health():
    """Endpoint for health check."""
    response = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }
    logger.debug(f"Health check: {response}")
    return jsonify(response), 200

@app.errorhandler(404)
def not_found(error):
    """Error handler 404."""
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Error handler 500."""
    logger.error(f"500 Internal Server Error: {str(error)}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    logger.info(f'Starting DevOps Info Service on {HOST}:{PORT} (debug={DEBUG})')
    app.run(host=HOST, port=PORT, debug=DEBUG)