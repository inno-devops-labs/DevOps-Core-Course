"""
DevOps Info Service
Main application module providing system information and health check.
"""
import os
import socket
import platform
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 3000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time for uptime calculation
START_TIME = datetime.now(timezone.utc)


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
    delta = datetime.now(timezone.utc) - START_TIME
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
        'current_time': datetime.now(timezone.utc).isoformat(),
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
        'timestamp': datetime.now(timezone.utc).isoformat(),
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
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status_code': 500
    }), 500


if __name__ == '__main__':
    print("🚀 Starting DevOps Info Service...")
    print(f"📍 Server: http://{HOST}:{PORT}")
    print(f"📊 Debug mode: {DEBUG}")
    print(f"⏰ Started at: {START_TIME.isoformat()}")
    print("\nAvailable endpoints:")
    print("  GET /       - Service information")
    print("  GET /health - Health check")
    print("\n" + "="*50 + "\n")

    app.run(host=HOST, port=PORT, debug=DEBUG)
