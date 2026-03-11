"""
DevOps Info Service with Prometheus metrics
"""
import os
import platform
import socket
import time
import logging
import random
from datetime import datetime, timezone
from flask import Flask, jsonify, request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import psutil

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5050))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
APP_NAME = os.getenv("APP_NAME", "info-service")

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

request_counter = 0

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
        
        with system_info_duration.time():
            uptime_seconds = int(time.time() - start_time)
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60

            # Получаем информацию о процессе
            process = psutil.Process()
            memory_info = process.memory_info()
            
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
                    "/slow": "Endpoint with artificial delay for testing"
                }
            }

        logger.info("Main endpoint processed successfully")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in main endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/health")
def health_check():
    """Health endpoint"""
    endpoint_calls.labels(endpoint='/health').inc()
    
    response = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.time() - start_time)
    }
    return jsonify(response), 200

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
    logger.info(f"Starting {APP_NAME} on {HOST}:{PORT}")
    logger.info(f"Metrics available at http://{HOST}:{PORT}/metrics")
    app.run(host=HOST, port=PORT, debug=DEBUG)
