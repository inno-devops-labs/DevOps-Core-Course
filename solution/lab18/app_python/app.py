import json
import logging
import os
import platform
import tempfile
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from uvicorn import run

START_TIME = datetime.now()
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
RELEASE_VERSION = os.getenv("RELEASE_VERSION", "v1")


class JSONFormatter(logging.Formatter):
    """Render application logs as JSON for Loki/Grafana ingestion."""

    _reserved_fields = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in self._reserved_fields:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def setup_logging() -> logging.Logger:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    return logging.getLogger(__name__)


logger = setup_logging()

HTTP_REQUESTS_TOTAL = Counter(
    "app_http_requests_total",
    "Total number of HTTP requests handled by the application.",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "app_http_request_duration_seconds",
    "HTTP request processing duration in seconds.",
    ["method", "endpoint"],
)
HTTP_ACTIVE_REQUESTS = Gauge(
    "app_http_active_requests",
    "Current number of in-flight HTTP requests.",
)
ROOT_REQUESTS_TOTAL = Counter(
    "app_root_requests_total",
    "Total number of calls to the root endpoint.",
)
SYSTEM_INFO_DURATION_SECONDS = Histogram(
    "app_system_info_duration_seconds",
    "System information collection duration in seconds.",
)
UPTIME_SECONDS = Gauge(
    "app_uptime_seconds",
    "Application uptime in seconds.",
)


class VisitStore:
    """Store visits in a file with a process-local lock and atomic writes."""

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self._lock = Lock()

    def initialize(self) -> None:
        with self._lock:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists():
                self._write_unlocked(0)

    def current(self) -> int:
        with self._lock:
            return self._read_unlocked()

    def increment(self) -> int:
        with self._lock:
            value = self._read_unlocked() + 1
            self._write_unlocked(value)
            return value

    def _read_unlocked(self) -> int:
        if not self.file_path.exists():
            return 0

        raw_value = self.file_path.read_text(encoding="utf-8").strip()
        if not raw_value:
            return 0

        try:
            return int(raw_value)
        except ValueError:
            logger.warning(
                "Invalid visits file content, resetting counter",
                extra={"event": "visits_file_invalid", "visits_file": str(self.file_path)},
            )
            return 0

    def _write_unlocked(self, value: int) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            dir=self.file_path.parent,
            encoding="utf-8",
        ) as temp_file:
            temp_file.write(str(value))
            temp_path = Path(temp_file.name)

        os.replace(temp_path, self.file_path)


def load_app_config(config_path: Path, visits_file: Path) -> dict:
    default_config = {
        "applicationName": "devops-info-service",
        "environment": "local",
        "featureFlags": {
            "visitsEndpoint": True,
            "configFromConfigMap": False,
        },
        "settings": {
            "visitsFile": str(visits_file),
        },
    }

    if not config_path.exists():
        return default_config

    try:
        loaded_config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning(
            "Unable to load configuration file, using defaults",
            extra={"event": "config_load_failed", "config_path": str(config_path)},
        )
        return default_config

    return {
        **default_config,
        **loaded_config,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    visits_file = Path(os.getenv("VISITS_FILE", "/data/visits"))
    config_path = Path(os.getenv("CONFIG_PATH", "/config/config.json"))

    app.state.visits_file = visits_file
    app.state.config_path = config_path
    app.state.visit_store = VisitStore(visits_file)
    app.state.visit_store.initialize()
    app.state.app_config = load_app_config(config_path, visits_file)

    logger.info(
        "Application startup",
        extra={
            "event": "startup",
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
            "release_version": RELEASE_VERSION,
            "service": "devops-info-service",
            "visits_file": str(visits_file),
            "config_path": str(config_path),
        },
    )
    yield
    logger.info("Application shutdown", extra={"event": "shutdown"})


app = FastAPI(lifespan=lifespan)


def get_uptime() -> dict:
    delta = datetime.now() - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }


UPTIME_SECONDS.set_function(lambda: get_uptime()["seconds"])


def get_endpoint_label(request: Request) -> str:
    route = request.scope.get("route")
    if route and getattr(route, "path", None):
        return route.path
    return request.url.path


def collect_system_info() -> dict:
    with SYSTEM_INFO_DURATION_SECONDS.time():
        return {
            "hostname": platform.node(),
            "platform": platform.system(),
            "platform_version": platform.release(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        }


@app.middleware("http")
async def log_requests(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.perf_counter()
    track_metrics = request.url.path != "/metrics"
    extra = {
        "event": "http_request",
        "method": request.method,
        "path": request.url.path,
        "client_ip": client_ip,
        "user_agent": request.headers.get("user-agent", ""),
    }

    logger.info("HTTP request started", extra=extra)
    if track_metrics:
        HTTP_ACTIVE_REQUESTS.inc()

    try:
        response = await call_next(request)
        return response
    except Exception:
        logger.exception("HTTP request failed", extra=extra)
        if track_metrics:
            endpoint = get_endpoint_label(request)
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=endpoint,
                status_code="500",
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(time.perf_counter() - start_time)
        raise
    finally:
        if track_metrics and "response" in locals():
            endpoint = get_endpoint_label(request)
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=str(response.status_code),
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(time.perf_counter() - start_time)
            logger.info(
                "HTTP request completed",
                extra={**extra, "status_code": response.status_code},
            )
        elif "response" in locals():
            logger.info(
                "HTTP request completed",
                extra={**extra, "status_code": response.status_code},
            )

        if track_metrics:
            HTTP_ACTIVE_REQUESTS.dec()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> HTMLResponse:
    """Default page for error display."""

    logger.warning(
        "HTTP exception handled",
        extra={
            "event": "http_exception",
            "method": request.method,
            "path": request.url.path,
            "status_code": exc.status_code,
            "client_ip": request.client.host if request.client else "unknown",
            "error": exc.detail,
        },
    )
    return HTMLResponse(
        content=f"<h1>Error {exc.status_code}</h1><p>{exc.detail}</p>",
        status_code=exc.status_code,
    )


@app.get("/", description="System and service info about the server")
async def root(request: Request) -> JSONResponse:
    """System and service info about the server."""

    ROOT_REQUESTS_TOTAL.inc()
    visits_count = request.app.state.visit_store.increment()

    return JSONResponse(
        status_code=200,
        content={
            "service": {
                "name": "devops-info-service",
                "version": "1.1.0",
                "description": "DevOps course info service",
                "framework": "FastAPI",
            },
            "system": collect_system_info(),
            "runtime": {
                "uptime_seconds": get_uptime()["seconds"],
                "uptime_human": get_uptime()["human"],
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": datetime.now().strftime("%Z"),
            },
            "configuration": {
                "file_path": str(request.app.state.config_path),
                "file_exists": request.app.state.config_path.exists(),
                "content": request.app.state.app_config,
                "environment_variables": {
                    "HOST": HOST,
                    "PORT": str(PORT),
                    "DEBUG": str(DEBUG).lower(),
                    "RELEASE_VERSION": RELEASE_VERSION,
                },
            },
            "visits": {
                "count": visits_count,
                "file_path": str(request.app.state.visits_file),
            },
            "request": {
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent"),
                "method": request.method,
                "path": request.url.path,
            },
            "endpoints": [
                {
                    "path": route.path,
                    "method": method,
                    "description": route.endpoint.__doc__ or "",
                }
                for route in request.app.routes
                for method in route.methods
            ],
        },
    )


@app.get("/visits", description="Current persisted visits counter")
async def visits(request: Request) -> JSONResponse:
    """Current persisted visits counter."""

    return JSONResponse(
        status_code=200,
        content={
            "count": request.app.state.visit_store.current(),
            "file_path": str(request.app.state.visits_file),
        },
    )


@app.get("/health", description="Service health chek")
async def health(request: Request) -> JSONResponse:
    """Service health-chek."""

    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "uptime_seconds": get_uptime()["seconds"],
        },
    )


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    run(app, port=PORT, host=HOST)
