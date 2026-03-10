"""
DevOps Info Service
Main application module providing system and service information
"""
import os
import socket
import platform
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request, g
from pythonjsonlogger import jsonlogger

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

# ── Request / response logging hooks ─────────────────────────────────────────
@app.before_request
def log_request():
    g.start_time = datetime.now(timezone.utc)
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

# Application start time
START_TIME = datetime.now(timezone.utc)

# Service metadata
SERVICE_INFO = {
    'name': 'devops-info-service',
    'version': '1.0.0',
    'description': 'DevOps course info service',
    'framework': 'Flask'
}


def get_system_info():
    """
    Collect system information.
    
    Returns:
        dict: System information including hostname, platform, architecture, etc.
    """
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
