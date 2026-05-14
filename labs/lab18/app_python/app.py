import os
import socket
import platform
import logging
import json
import time
import copy
import fcntl
from pathlib import Path
from threading import Lock
from datetime import datetime, timezone
from flask import Flask, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

app = Flask(__name__)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

SERVICE_NAME = os.getenv("SERVICE_NAME", "devops-info-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
SERVICE_DESCRIPTION = os.getenv("SERVICE_DESCRIPTION", "DevOps course info service")
SERVICE_FRAMEWORK = os.getenv("SERVICE_FRAMEWORK", "Flask")

START_TIME = datetime.now(timezone.utc)
CONFIG_PATH_ENV = "APP_CONFIG_PATH"
VISITS_FILE_PATH_ENV = "VISITS_FILE_PATH"
DEFAULT_CONFIG_PATH = "/config/config.json"
DEFAULT_VISITS_FILE_PATH = "/data/visits"
DEFAULT_FILE_CONFIG = {
    "application": {
        "name": SERVICE_NAME,
        "environment": "dev",
        "feature_flags": {
            "show_hostname": True,
            "show_request_headers": False,
        },
        "settings": {
            "greeting": "Welcome to the DevOps info service",
            "log_level": "INFO",
        },
    }
}
_config_cache = {
    "path": None,
    "mtime_ns": None,
    "data": copy.deepcopy(DEFAULT_FILE_CONFIG),
}
_runtime_lock = Lock()
_runtime_initialized = False

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
)
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)
devops_info_endpoint_calls_total = Counter(
    "devops_info_endpoint_calls_total",
    "Total calls to application endpoints",
    ["endpoint"],
)
devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information",
)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in {
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
                "taskName",
                "thread",
                "threadName",
            }:
                continue
            payload[key] = value
        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    return logging.getLogger("devops-info-service")


logger = configure_logging()


def get_config_path():
    return Path(os.getenv(CONFIG_PATH_ENV, DEFAULT_CONFIG_PATH))


def get_visits_file_path():
    return Path(os.getenv(VISITS_FILE_PATH_ENV, DEFAULT_VISITS_FILE_PATH))


def normalize_bool(value, default):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    if value is None:
        return default
    return bool(value)


def get_env_value(name):
    value = os.getenv(name)
    return value if value not in {None, ""} else None


def normalize_file_config(raw_config):
    application = raw_config.get("application", {}) if isinstance(raw_config, dict) else {}
    feature_flags = application.get("feature_flags", {}) if isinstance(application, dict) else {}
    settings = application.get("settings", {}) if isinstance(application, dict) else {}
    defaults = DEFAULT_FILE_CONFIG["application"]
    return {
        "application": {
            "name": str(application.get("name", defaults["name"])),
            "environment": str(application.get("environment", defaults["environment"])),
            "feature_flags": {
                "show_hostname": normalize_bool(
                    feature_flags.get(
                        "show_hostname",
                        defaults["feature_flags"]["show_hostname"],
                    ),
                    defaults["feature_flags"]["show_hostname"],
                ),
                "show_request_headers": normalize_bool(
                    feature_flags.get(
                        "show_request_headers",
                        defaults["feature_flags"]["show_request_headers"],
                    ),
                    defaults["feature_flags"]["show_request_headers"],
                ),
            },
            "settings": {
                "greeting": str(settings.get("greeting", defaults["settings"]["greeting"])),
                "log_level": str(settings.get("log_level", defaults["settings"]["log_level"])).upper(),
            },
        }
    }


def load_file_config():
    config_path = get_config_path()
    try:
        stat = config_path.stat()
    except FileNotFoundError:
        if _config_cache["path"] != config_path or _config_cache["mtime_ns"] is not None:
            logger.warning(
                "config_file_missing",
                extra={"config_path": str(config_path)},
            )
        _config_cache["path"] = config_path
        _config_cache["mtime_ns"] = None
        _config_cache["data"] = copy.deepcopy(DEFAULT_FILE_CONFIG)
        return _config_cache["data"]

    if _config_cache["path"] == config_path and _config_cache["mtime_ns"] == stat.st_mtime_ns:
        return _config_cache["data"]

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            loaded = json.load(config_file)
    except (OSError, json.JSONDecodeError) as error:
        logger.warning(
            "config_file_invalid",
            extra={
                "config_path": str(config_path),
                "error": str(error),
            },
        )
        loaded = copy.deepcopy(DEFAULT_FILE_CONFIG)

    _config_cache["path"] = config_path
    _config_cache["mtime_ns"] = stat.st_mtime_ns
    _config_cache["data"] = normalize_file_config(loaded)
    return _config_cache["data"]


def get_application_configuration():
    file_config = load_file_config()["application"]
    environment = get_env_value("APP_ENV") or file_config["environment"]
    greeting = file_config["settings"]["greeting"]
    log_level = (get_env_value("APP_LOG_LEVEL") or file_config["settings"]["log_level"]).upper()
    feature_show_hostname = file_config["feature_flags"]["show_hostname"]
    feature_show_request_headers = file_config["feature_flags"]["show_request_headers"]
    return {
        "name": file_config["name"],
        "environment": environment,
        "feature_flags": {
            "show_hostname": feature_show_hostname,
            "show_request_headers": feature_show_request_headers,
        },
        "settings": {
            "greeting": greeting,
            "log_level": log_level,
        },
        "config_path": str(get_config_path()),
    }


def apply_log_level(level_name):
    resolved_level = getattr(logging, level_name.upper(), logging.INFO)
    logging.getLogger().setLevel(resolved_level)
    logger.setLevel(resolved_level)


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


def get_system_info(application_config):
    return {
        "hostname": socket.gethostname() if application_config["feature_flags"]["show_hostname"] else None,
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_service_info():
    return {
        "name": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": SERVICE_DESCRIPTION,
        "framework": SERVICE_FRAMEWORK,
    }


def get_runtime_info():
    uptime = get_uptime()
    return {
        "uptime_seconds": uptime["seconds"],
        "uptime_human": uptime["human"],
        "current_time": datetime.now(timezone.utc).isoformat(),
        "timezone": "UTC",
    }


def get_request_info(req):
    request_info = {
        "client_ip": req.remote_addr,
        "user_agent": req.headers.get("User-Agent", "Unknown"),
        "method": req.method,
        "path": req.path,
    }
    application_config = get_application_configuration()
    if application_config["feature_flags"]["show_request_headers"]:
        request_info["headers"] = dict(req.headers.items())
    return request_info


def get_endpoints():
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/visits", "method": "GET", "description": "Current visits counter"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
    ]


def ensure_visits_storage():
    visits_file_path = get_visits_file_path()
    visits_file_path.parent.mkdir(parents=True, exist_ok=True)
    if not visits_file_path.exists():
        with visits_file_path.open("w", encoding="utf-8") as visits_file:
            visits_file.write("0\n")
    return visits_file_path


def parse_visits_count(raw_value):
    try:
        return max(int(raw_value.strip() or "0"), 0)
    except ValueError:
        logger.warning(
            "visits_file_invalid",
            extra={
                "visits_file_path": str(get_visits_file_path()),
                "raw_value": raw_value,
            },
        )
        return 0


def read_visits_count():
    visits_file_path = ensure_visits_storage()
    with visits_file_path.open("a+", encoding="utf-8") as visits_file:
        fcntl.flock(visits_file.fileno(), fcntl.LOCK_SH)
        visits_file.seek(0)
        current_count = parse_visits_count(visits_file.read())
        fcntl.flock(visits_file.fileno(), fcntl.LOCK_UN)
    return current_count


def increment_visits_count():
    visits_file_path = ensure_visits_storage()
    with visits_file_path.open("a+", encoding="utf-8") as visits_file:
        fcntl.flock(visits_file.fileno(), fcntl.LOCK_EX)
        visits_file.seek(0)
        current_count = parse_visits_count(visits_file.read())
        updated_count = current_count + 1
        visits_file.seek(0)
        visits_file.truncate()
        visits_file.write(f"{updated_count}\n")
        visits_file.flush()
        os.fsync(visits_file.fileno())
        fcntl.flock(visits_file.fileno(), fcntl.LOCK_UN)
    return updated_count


def ensure_runtime_initialized():
    global _runtime_initialized
    if _runtime_initialized:
        return
    with _runtime_lock:
        if _runtime_initialized:
            return
        current_configuration = get_application_configuration()
        apply_log_level(current_configuration["settings"]["log_level"])
        current_visits = read_visits_count()
        logger.info(
            "runtime_initialized",
            extra={
                "config_path": current_configuration["config_path"],
                "environment": current_configuration["environment"],
                "visits_file_path": str(get_visits_file_path()),
                "visits_count": current_visits,
            },
        )
        _runtime_initialized = True


def build_request_context(status_code=None):
    context = {
        "service": SERVICE_NAME,
        "client_ip": request.remote_addr,
        "method": request.method,
        "path": request.path,
        "user_agent": request.headers.get("User-Agent", "Unknown"),
    }
    if status_code is not None:
        context["status_code"] = status_code
    if hasattr(g, "request_started_at"):
        context["duration_ms"] = round((time.perf_counter() - g.request_started_at) * 1000, 2)
    return context


def get_endpoint_label():
    if request.url_rule is not None and request.url_rule.rule:
        return request.url_rule.rule
    return request.path or "unknown"


@app.before_request
def before_request():
    ensure_runtime_initialized()
    apply_log_level(get_application_configuration()["settings"]["log_level"])
    g.request_started_at = time.perf_counter()
    g.metrics_endpoint = get_endpoint_label()
    g.metrics_method = request.method
    g.metrics_gauge_incremented = True
    http_requests_in_progress.labels(method=g.metrics_method, endpoint=g.metrics_endpoint).inc()
    logger.info("request_started", extra=build_request_context())


@app.after_request
def after_request(response):
    context = build_request_context(response.status_code)
    endpoint = getattr(g, "metrics_endpoint", get_endpoint_label())
    method = getattr(g, "metrics_method", request.method)
    status_code = str(response.status_code)
    duration_seconds = max(time.perf_counter() - g.request_started_at, 0.0)
    http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code,
    ).observe(duration_seconds)
    if response.status_code >= 500:
        logger.error("request_finished", extra=context)
    elif response.status_code >= 400:
        logger.warning("request_finished", extra=context)
    else:
        logger.info("request_finished", extra=context)
    return response


@app.teardown_request
def teardown_request(error):
    if getattr(g, "metrics_gauge_incremented", False):
        http_requests_in_progress.labels(
            method=getattr(g, "metrics_method", request.method),
            endpoint=getattr(g, "metrics_endpoint", get_endpoint_label()),
        ).dec()
        g.metrics_gauge_incremented = False


@app.route("/")
def index():
    devops_info_endpoint_calls_total.labels(endpoint="/").inc()
    start_time = time.perf_counter()
    application_config = get_application_configuration()
    visits_count = increment_visits_count()
    system_info = get_system_info(application_config)
    devops_info_system_collection_seconds.observe(max(time.perf_counter() - start_time, 0.0))
    response = {
        "message": application_config["settings"]["greeting"],
        "service": get_service_info(),
        "system": system_info,
        "runtime": get_runtime_info(),
        "request": get_request_info(request),
        "configuration": application_config,
        "visits": {
            "count": visits_count,
            "file_path": str(get_visits_file_path()),
        },
        "endpoints": get_endpoints(),
    }
    return jsonify(response)


@app.route("/visits")
def visits():
    devops_info_endpoint_calls_total.labels(endpoint="/visits").inc()
    return jsonify(
        {
            "count": read_visits_count(),
            "file_path": str(get_visits_file_path()),
        }
    )


@app.route("/health")
def health():
    devops_info_endpoint_calls_total.labels(endpoint="/health").inc()
    response = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": get_uptime()["seconds"],
    }
    return jsonify(response)


@app.route("/metrics")
def metrics():
    devops_info_endpoint_calls_total.labels(endpoint="/metrics").inc()
    return app.response_class(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.errorhandler(404)
def not_found(error):
    logger.warning("endpoint_not_found", extra=build_request_context(404))
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.exception("internal_server_error", extra=build_request_context(500))
    return (
        jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
            }
        ),
        500,
    )


if __name__ == "__main__":
    ensure_runtime_initialized()
    logger.info(
        "application_starting",
        extra={
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
        },
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)


#   ██████████████    ██████████      ██  ██    ██      ██████████████
#   ██          ██        ██████  ██  ████  ██████  ██  ██          ██
#   ██  ██████  ██  ██  ██  ██    ██        ██████      ██  ██████  ██
#   ██  ██████  ██  ████████      ██████    ██  ██      ██  ██████  ██
#   ██  ██████  ██  ████  ██  ██    ████  ██  ██        ██  ██████  ██
#   ██          ██  ████  ██    ██████  ██              ██          ██
#   ██████████████  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██████████████
#                   ██    ████  ██  ██    ██  ██  ████
#   ██  ██████████        ████  ██    ████████  ██      ██████████
#       ██  ██      ████    ████    ██  ██  ██    ████████    ██  ██
#       ██████  ██  ████  ██████████    ██    ██    ██    ██    ████
#     ██              ██      ██        ██  ██████          ██████
#     ██        ██    ██████    ████  ████████  ████████    ██████  ██
#       ██████    ████  ██            ██████    ████  ██  ██        ██
#     ██  ████  ██    ██        ████    ██  ██      ██    ████
#   ██  ██    ██    ██  ████    ██████        ████              ██████
#           ██████  ██        ██  ██████        ████  ██  ████      ██
#     ██████████      ██  ██        ████████████  ██████████  ██
#       ██  ██  ██        ██████████████    ██        ████        ██
#         ██  ██  ██████████████  ██    ████████    ██  ████  ████████
#   ██    ████  ██    ██    ████████      ██          ██    ██  ██
#   ██  ████████        ██████  ██████    ██  ██  ████    ██  ██    ██
#   ██  ████    ████  ██  ████    ██████      ██    ██        ████
#   ██  ████          ██    ████████    ██    ██████      ██  ██████
#   ██  ██  ██  ██  ██              ██████  ██      ██████████    ████
#                   ██  ████  ████  ██  ████  ████  ██      ██  ██  ██
#   ██████████████      ████████  ██  ████        ████  ██  ████
#   ██          ██  ██    ██        ██  ██  ██████  ██      ██  ██████
#   ██  ██████  ██  ████      ██  ██  ██████  ████  ██████████      ██
#   ██  ██████  ██  ██  ████    ██        ████    ██████  ██    ██████
#   ██  ██████  ██  ██████  ████████████    ██████      ██      ██
#   ██          ██                      ██  ██████    ████      ██
#   ██████████████  ████  ██████  ██  ██████  ████  ██    ██████  ██
