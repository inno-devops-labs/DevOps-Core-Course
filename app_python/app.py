import os
import fastapi
from datetime import datetime, timezone
import uvicorn
import logging
import json
import time

from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST


VISITS_FILE = "/data/visits"

app = fastapi.FastAPI()


http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"]
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Requests in progress"
)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        })


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False


start_time = datetime.now()


def get_uptime():
    delta = datetime.now() - start_time
    seconds = int(delta.total_seconds())
    return {"seconds": seconds}


def get_system():
    import platform
    import socket

    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "python": platform.python_version(),
    }


def read_visits():
    try:
        if not os.path.exists(VISITS_FILE):
            return 0
        with open(VISITS_FILE, "r") as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0


def write_visits(count):
    try:
        os.makedirs("/data", exist_ok=True)
        with open(VISITS_FILE, "w") as f:
            f.write(str(count))
    except Exception as e:
        logger.error(f"Failed to write visits: {e}")


@app.middleware("http")
async def metrics_middleware(request: fastapi.Request, call_next):
    method = request.method
    endpoint = request.url.path

    http_requests_in_progress.inc()
    start = time.time()

    try:
        response = await call_next(request)
        status = response.status_code
        return response

    except Exception:
        status = 500
        raise

    finally:
        duration = time.time() - start

        http_requests_total.labels(method, endpoint, status).inc()
        http_request_duration_seconds.labels(method, endpoint).observe(duration)
        http_requests_in_progress.dec()



@app.get("/")
def root(request: fastapi.Request):
    visits = read_visits()
    visits += 1
    write_visits(visits)

    return {
        "service": "devops-info-service",
        "system": get_system(),
        "uptime": get_uptime(),
        "client": request.client.host,
        "visits": visits
    }


@app.get("/visits")
def get_visits():
    return {
        "visits": read_visits()
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def start():
    uvicorn.run(app, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    start()