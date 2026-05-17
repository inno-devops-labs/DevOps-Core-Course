import os
import socket
import platform
import logging
import json
from datetime import datetime, timezone
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
START_TIME = datetime.now(timezone.utc)

# Paths for persistence and configuration
DATA_DIR = os.getenv('DATA_DIR', '../data')
CONFIG_DIR = os.getenv('CONFIG_DIR', '/config')
VISITS_FILE = os.path.join(DATA_DIR, 'visits')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

def load_config():
    """Load configuration from JSON file"""
    default_config = {
        "app_name": "devops-info-service",
        "environment": "development",
        "features": {
            "visits_counter": True,
            "metrics": False
        }
    }
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            logger.info(f"Configuration loaded from {CONFIG_FILE}")
            return config
    except FileNotFoundError:
        logger.warning(f"Config file {CONFIG_FILE} not found, using defaults")
        return default_config
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config: {e}")
        return default_config

def load_visits():
    """Load visit counter from file"""
    try:
        with open(VISITS_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        logger.info(f"Visits file not found, starting at 0")
        return 0

def save_visits(count):
    """Save visit counter to file"""
    try:
        with open(VISITS_FILE, 'w') as f:
            f.write(str(count))
        logger.debug(f"Saved visits: {count}")
    except IOError as e:
        logger.error(f"Error saving visits: {e}")

def increment_visits():
    """Increment visit counter"""
    count = load_visits() + 1
    save_visits(count)
    return count

def get_system_info():
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.release(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }

def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return {
        'seconds': seconds,
        'human': f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    }

@app.route('/', methods=['GET'])
def index():
    logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
    
    # Increment visit counter
    visits = increment_visits()
    
    uptime = get_uptime()
    config = load_config()
    
    return jsonify({
        "service": {
            "name": config.get("app_name", "devops-info-service"),
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
            "environment": config.get("environment", "unknown")
        },
        "visits": {
            "count": visits,
            "message": f"You are visitor #{visits}"
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime['seconds'],
            "uptime_human": uptime['human'],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC"
        },
        "request": {
            "client_ip": request.remote_addr or 'unknown',
            "user_agent": request.headers.get('User-Agent', 'unknown'),
            "method": request.method,
            "path": request.path
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information (increments visit counter)"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Current visit count"}
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds'],
        'config_file': os.path.exists(CONFIG_FILE),
        'visits_file': os.path.exists(VISITS_FILE)
    })

@app.route('/visits', methods=['GET'])
def get_visits():
    """Endpoint to get current visit count"""
    count = load_visits()
    return jsonify({
        'count': count,
        'message': f"Total visits: {count}",
        'file_path': VISITS_FILE,
        'persistent': os.path.exists(VISITS_FILE)
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': 'Endpoint does not exist'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    logger.info('Application starting...')
    logger.info(f'Data directory: {DATA_DIR}')
    logger.info(f'Config directory: {CONFIG_DIR}')
    app.run(host=HOST, port=PORT, debug=False)