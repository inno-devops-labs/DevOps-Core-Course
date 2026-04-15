import logging
import json
import os
import platform
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, Response
from prometheus_client import CollectorRegistry, Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Use custom registry to avoid conflicts with uvicorn/other libs that may register metrics
METRICS_REGISTRY = CollectorRegistry()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

_visits_lock = threading.Lock()


def _visits_path() -> Path:
    """Path to the visit counter file (Lab 12 persistence)."""
    return Path(os.getenv("VISITS_FILE", "/data/visits"))


def _config_json_path() -> Path:
    """Optional mounted ConfigMap file (Lab 12)."""
    return Path(os.getenv("CONFIG_JSON_PATH", "/config/config.json"))


def load_mounted_config() -> dict:
    """Load JSON from CONFIG_JSON_PATH if the file exists."""
    path = _config_json_path()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logging.getLogger(__name__).warning(
            "Could not read config file", extra={"path": str(path), "error": str(e)}
        )
        return {}


def read_visits() -> int:
    path = _visits_path()
    try:
        content = path.read_text(encoding="utf-8").strip()
        return int(content) if content else 0
    except FileNotFoundError:
        return 0
    except (ValueError, OSError):
        return 0


def write_visits(count: int) -> None:
    path = _visits_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(str(count), encoding="utf-8")
    tmp.replace(path)


def increment_visits() -> int:
    with _visits_lock:
        n = read_visits() + 1
        write_visits(n)
        return n


class JSONFormatter(logging.Formatter):
    """Format log records as structured JSON for Loki/Promtail."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        log = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include any custom attributes (e.g., request context) that don't start with "_"
        for key, value in record.__dict__.items():
            if key.startswith("_"):
                continue
            if key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }:
                continue
            log[key] = value

        if record.exc_info:
            log["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log, ensure_ascii=False)


root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Remove default handlers configured by other libraries/tests
for handler in list(root_logger.handlers):
    root_logger.removeHandler(handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(JSONFormatter())
root_logger.addHandler(stream_handler)

logger = logging.getLogger(__name__)

# Prometheus metrics (RED method: Rate, Errors, Duration)
# Use METRICS_REGISTRY to avoid conflicts with default registry (uvicorn/other libs)
http_requests_total = Counter(
    "devops_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=METRICS_REGISTRY,
)

http_request_duration_seconds = Histogram(
    "devops_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=METRICS_REGISTRY,
)

http_requests_in_progress = Gauge(
    "devops_http_requests_in_progress",
    "HTTP requests currently being processed",
    registry=METRICS_REGISTRY,
)

# Application-specific metrics
devops_info_endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "Endpoint calls for DevOps info service",
    ["endpoint"],
    registry=METRICS_REGISTRY,
)

devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection time in seconds",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=METRICS_REGISTRY,
)


def _normalize_endpoint(path: str) -> str:
    """Normalize endpoint for low cardinality (avoid user IDs etc.)."""
    if path == "/":
        return "/"
    if path in ("/health", "/metrics", "/visits"):
        return path
    return path


app = FastAPI(title="DevOps Info Service")
START_TIME = datetime.now(timezone.utc)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log each HTTP request and response in JSON format; record Prometheus metrics."""
    start_time = time.time()
    endpoint = _normalize_endpoint(request.url.path)
    http_requests_in_progress.inc()

    try:
        response = await call_next(request)
        status = str(response.status_code)
    except Exception:
        duration_s = time.time() - start_time
        status = "500"
        http_requests_total.labels(method=request.method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(method=request.method, endpoint=endpoint).observe(duration_s)
        http_requests_in_progress.dec()
        logger.exception(
            "Request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "duration_ms": round(duration_s * 1000, 2),
            },
        )
        raise

    duration_s = time.time() - start_time
    http_requests_total.labels(method=request.method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=request.method, endpoint=endpoint).observe(duration_s)
    http_requests_in_progress.dec()

    if endpoint in ("/", "/health", "/visits"):
        devops_info_endpoint_calls.labels(endpoint=endpoint).inc()
        devops_info_system_collection_seconds.observe(duration_s)

    duration_ms = duration_s * 1000
    logger.info(
        "Request handled",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": request.client.host if request.client else None,
            "duration_ms": round(duration_ms, 2),
        },
    )
    return response

def get_runtime_info():
    """Calculate uptime and current time metrics."""
    now = datetime.now(timezone.utc)
    delta = now - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return {
        "uptime_seconds": seconds,
        "uptime_human": f"{hours} hours, {minutes} minutes",
        "current_time": now.isoformat(),
        "timezone": "UTC",
    }
@app.get("/", tags=["Info"])
async def read_root(request: Request):
    """Main endpoint returning comprehensive service and system information."""
    logger.info(
        "Root endpoint called",
        extra={
            "client_ip": request.client.host if request.client else None,
            "method": request.method,
            "path": request.url.path,
        },
    )
    try:
        visit_total = increment_visits()
        mounted = load_mounted_config()
        app_name = mounted.get("applicationName", "devops-info-service")
        env_label = mounted.get("environment", "development")
        return {
            "service": {
                "name": app_name,
                "version": "1.0.0",
                "description": "DevOps course info service",
                "framework": "FastAPI",
                "environment": env_label,
                "mountedConfig": mounted if mounted else None,
            },
            "system": {
                "hostname": socket.gethostname(),
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "cpu_count": os.cpu_count() or "unknown",
                "python_version": platform.python_version(),
            },
            "runtime": get_runtime_info(),
            "visits": {
                "total": visit_total,
                "file": str(_visits_path()),
            },
            "request": {
                "client_ip": request.client.host,
                "user_agent": request.headers.get("User-Agent"),
                "method": request.method,
                "path": request.url.path
            },
            "endpoints": [
                {"path": "/", "method": "GET", "description": "Service information (increments visit counter)"},
                {"path": "/visits", "method": "GET", "description": "Current visit counter"},
                {"path": "/health", "method": "GET", "description": "Health check"},
                {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
            ],
        }
    except Exception as e:
        logger.error(
            "Error in root endpoint",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/visits", tags=["Info"])
async def visits():
    """Return the current persisted visit counter (Lab 12)."""
    return {"visits": read_visits(), "file": str(_visits_path())}


@app.get("/health", tags=["Monitoring"])
async def health():
    """Simple health check endpoint for monitoring."""
    runtime = get_runtime_info()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": runtime["uptime_seconds"],
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint for scraping."""
    return Response(
        content=generate_latest(METRICS_REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": f"Endpoint {request.url.path} does not exist"}
    )

if __name__ == "__main__":
    logger.info(
        "Starting service",
        extra={
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
        },
    )
    uvicorn.run("app:app", host=HOST, port=PORT, reload=DEBUG)
