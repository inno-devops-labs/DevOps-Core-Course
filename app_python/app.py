"""
DevOps Info Service with Prometheus metrics and Vault integration
"""
import os
import platform
import socket
import time
import logging
import random
import json
import fcntl
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import psutil

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5050))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
APP_NAME = os.getenv("APP_NAME", "info-service")
VAULT_ENABLED = os.getenv("VAULT_ENABLED", "false").lower() == "true"
VAULT_SECRETS_PATH = os.getenv("VAULT_SECRETS_PATH", "/vault/secrets")

VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits.txt")

app = Flask(__name__)
start_time = time.time()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently being processed'
)

endpoint_calls = Counter(
    'devops_info_endpoint_calls_total',
    'Number of calls to each endpoint',
    ['endpoint']
)

system_info_duration = Histogram(
    'devops_info_system_collection_seconds',
    'Time taken to collect system information',
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1)
)

process_memory_bytes = Gauge(
    'process_memory_bytes',
    'Memory usage of the Python process in bytes'
)

vault_secrets_info = Gauge(
    'vault_secrets_info',
    'Information about Vault secrets',
    ['format', 'version']
)

visits_total = Counter(
    'visits_total',
    'Total number of visits to the root endpoint'
)

request_counter = 0

def read_visits():
    """Read visits count from file with locking"""
    try:
        os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
        
        with open(VISITS_FILE, 'a+') as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            f.seek(0)
            content = f.read().strip()
            fcntl.flock(f, fcntl.LOCK_UN)
            
            if content:
                return int(content)
            return 0
    except Exception as e:
        logger.error(f"Error reading visits file: {e}")
        return 0

def write_visits(count):
    """Write visits count to file with locking"""
    try:
        with open(VISITS_FILE, 'w') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(str(count))
            fcntl.flock(f, fcntl.LOCK_UN)
        return True
    except Exception as e:
        logger.error(f"Error writing visits file: {e}")
        return False

def increment_visits():
    """Increment visits count atomically"""
    current = read_visits()
    new_count = current + 1
    if write_visits(new_count):
        visits_total.inc()
        return new_count
    return current

def load_vault_secrets():
    """Load secrets from Vault injected files"""
    secrets = {
        "env": {},
        "json": None,
        "yaml": None,
        "formats": []
    }
    
    vault_path = Path(VAULT_SECRETS_PATH)
    
    if not vault_path.exists():
        logger.info("Vault secrets path not found, skipping")
        return secrets
    
    env_file = vault_path / ".env"
    if env_file.exists():
        logger.info("Loading secrets from .env file")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith('export ') and '=' in line:
                    parts = line.replace('export ', '', 1).split('=', 1)
                    if len(parts) == 2:
                        key, value = parts
                        value = value.strip().strip('"').strip("'")
                        secrets["env"][key] = value
                        os.environ[key] = value
        secrets["formats"].append("env")
        vault_secrets_info.labels(format='env', version='1').set(1)
    
    json_file = vault_path / "config.json"
    if json_file.exists():
        logger.info("Loading secrets from config.json")
        try:
            with open(json_file) as f:
                secrets["json"] = json.load(f)
            secrets["formats"].append("json")
            vault_secrets_info.labels(format='json', version='1').set(1)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
    
    yaml_file = vault_path / "config.yaml"
    if yaml_file.exists():
        logger.info("Loading secrets from config.yaml")
        try:
            with open(yaml_file) as f:
                secrets["yaml"] = yaml.safe_load(f)
            secrets["formats"].append("yaml")
            vault_secrets_info.labels(format='yaml', version='1').set(1)
        except:
            logger.error(f"Failed to parse YAML: {e}")
    
    if secrets["json"] and "_metadata" in secrets["json"]:
        version = secrets["json"]["_metadata"].get("version", 1)
        vault_secrets_info.labels(format='json', version=str(version)).set(1)
    
    return secrets

def update_process_metrics():
    """Update process-level metrics"""
    try:
        process = psutil.Process()
        process_memory_bytes.set(process.memory_info().rss)
        logger.info("Process metrics updated")
    except Exception as e:
        logger.error(f"Failed to update process metrics: {e}")

@app.before_request
def before_request():
    """Track request start time and active requests"""
    request.start_time = time.time()
    http_requests_in_progress.inc()

@app.after_request
def after_request(response):
    """Record metrics after request completes"""
    global request_counter
    
    duration = time.time() - request.start_time
    
    if request.endpoint == 'metrics':
        endpoint = '/metrics'
    elif request.endpoint == 'static':
        endpoint = '/static'
    else:
        endpoint = request.path
    
    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status=response.status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)
    
    http_requests_in_progress.dec()
    
    request_counter += 1
    if request_counter % 10 == 0:
        update_process_metrics()
    
    return response

@app.route("/metrics")
def metrics_endpoint():
    """Prometheus metrics endpoint"""
    endpoint_calls.labels(endpoint='/metrics').inc()
    return Response(generate_latest(), mimetype='text/plain')

@app.route("/")
def main_info():
    """Main endpoint - service and system information"""
    endpoint_calls.labels(endpoint='/').inc()
    
    try:
        time.sleep(random.uniform(0.01, 0.1))
        
        visit_count = increment_visits()
        
        with system_info_duration.time():
            uptime_seconds = int(time.time() - start_time)
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60

            process = psutil.Process()
            memory_info = process.memory_info()
            
            vault_secrets = load_vault_secrets() if VAULT_ENABLED else {}
            
            db_password = os.getenv("db_password", os.getenv("DB_PASSWORD", "not-set"))
            api_key = os.getenv("api_key", os.getenv("API_KEY", "not-set"))
            
            response = {
                "service": {
                    "name": APP_NAME,
                    "version": "1.0.0",
                    "description": "DevOps course info service",
                    "framework": "Flask",
                    "uptime_seconds": uptime_seconds,
                    "uptime_human": f"{hours} hour(s), {minutes} minute(s)"
                },
                "system": {
                    "hostname": socket.gethostname(),
                    "platform": platform.system(),
                    "platform_version": platform.version(),
                    "architecture": platform.machine(),
                    "cpu_count": os.cpu_count(),
                    "python_version": platform.python_version()
                },
                "runtime": {
                    "start_time": start_time,
                    "current_time": time.time(),
                    "memory_usage_bytes": memory_info.rss,
                    "memory_usage_mb": round(memory_info.rss / (1024 * 1024), 2),
                    "cpu_percent": process.cpu_percent(interval=0.1)
                },
                "request": {
                    "client_ip": request.remote_addr,
                    "user_agent": request.headers.get("User-Agent"),
                    "method": request.method,
                    "path": request.path
                },
                "endpoints": {
                    "/": "Main service information",
                    "/health": "Health check endpoint",
                    "/metrics": "Prometheus metrics endpoint",
                    "/slow": "Endpoint with artificial delay for testing",
                    "/secrets": "Show Vault secrets info (if enabled)",
                    "/reload": "Trigger secrets reload (demo only)",
                    "/visits": "Show total visits count"
                },
                "visits": {
                    "total": visit_count
                }
            }
            
            if VAULT_ENABLED:
                response["vault"] = {
                    "enabled": True,
                    "secrets_path": VAULT_SECRETS_PATH,
                    "secrets_available": len(vault_secrets.get("env", {})) > 0,
                    "formats": vault_secrets.get("formats", []),
                    "env_keys": list(vault_secrets.get("env", {}).keys()),
                    "demo_values": vault_secrets.get("env", {}) if DEBUG else {
                        k: "***hidden***" for k in vault_secrets.get("env", {}).keys()
                    }
                }
                
                if vault_secrets.get("json"):
                    response["vault"]["json_metadata"] = vault_secrets["json"].get("_metadata", {})
                
                response["secrets_demo"] = {
                    "db_password_exists": db_password != "not-set",
                    "api_key_exists": api_key != "not-set",
                    "db_password_preview": db_password[:3] + "***" if db_password != "not-set" else "not-set"
                }

        logger.info(f"Main endpoint processed, visit #{visit_count}")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in main endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/visits")
def visits_endpoint():
    """Return current visits count"""
    endpoint_calls.labels(endpoint='/visits').inc()
    count = read_visits()
    return jsonify({
        "visits": count,
        "file": VISITS_FILE,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route("/health")
def health_check():
    """Health endpoint"""
    endpoint_calls.labels(endpoint='/health').inc()
    
    response = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.time() - start_time)
    }
    
    try:
        visits = read_visits()
        response["visits_file"] = {
            "path": VISITS_FILE,
            "exists": os.path.exists(VISITS_FILE),
            "readable": True,
            "current_count": visits
        }
    except Exception as e:
        response["visits_file"] = {
            "path": VISITS_FILE,
            "exists": False,
            "error": str(e)
        }
    
    if VAULT_ENABLED:
        vault_path = Path(VAULT_SECRETS_PATH)
        response["vault"] = {
            "secrets_mounted": vault_path.exists(),
            "secrets_files": [f.name for f in vault_path.glob("*")] if vault_path.exists() else []
        }
    
    return jsonify(response), 200

@app.route("/secrets")
def secrets_info():
    """Show secrets information (debug endpoint)"""
    endpoint_calls.labels(endpoint='/secrets').inc()
    
    if not VAULT_ENABLED:
        return jsonify({"error": "Vault integration not enabled"}), 404
    
    vault_secrets = load_vault_secrets()
    
    if DEBUG:
        return jsonify(vault_secrets)
    else:
        return jsonify({
            "enabled": True,
            "formats": vault_secrets.get("formats", []),
            "secrets_count": len(vault_secrets.get("env", {})),
            "json_available": vault_secrets.get("json") is not None,
            "yaml_available": vault_secrets.get("yaml") is not None
        })

@app.route("/reload", methods=["POST"])
def reload_secrets():
    """Force reload secrets (demo endpoint)"""
    endpoint_calls.labels(endpoint='/reload').inc()
    
    if not VAULT_ENABLED:
        return jsonify({"error": "Vault integration not enabled"}), 404
    
    secrets = load_vault_secrets()
    
    return jsonify({
        "status": "reloaded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "formats_found": secrets.get("formats", [])
    })

@app.route("/slow")
def slow_endpoint():
    """Slow endpoint for testing latency metrics"""
    endpoint_calls.labels(endpoint='/slow').inc()
    
    delay = random.uniform(0.5, 2.0)
    time.sleep(delay)
    
    return jsonify({
        "message": f"This request took {delay:.2f} seconds",
        "delay": delay
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    update_process_metrics()
    
    initial_count = read_visits()
    logger.info(f"Starting with visits count: {initial_count}")
    
    if VAULT_ENABLED:
        logger.info(f"Vault integration enabled, looking for secrets in {VAULT_SECRETS_PATH}")
        vault_secrets = load_vault_secrets()
        logger.info(f"Found secrets formats: {vault_secrets.get('formats', [])}")
    
    logger.info(f"Starting {APP_NAME} on {HOST}:{PORT}")
    logger.info(f"Metrics available at http://{HOST}:{PORT}/metrics")
    logger.info(f"Visits file: {VISITS_FILE}")
    logger.info(f"Debug mode: {DEBUG}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
