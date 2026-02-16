import datetime as dt
import pytz
import time
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from prometheus_client import Summary, Counter, generate_latest, CONTENT_TYPE_LATEST

# Initialize FastAPI app
app = FastAPI()

# Set up Jinja2 for rendering templates
templates = Jinja2Templates(directory="templates")


def get_moscow_time():
    """Returns the current time in Moscow as a dictionary."""
    now = dt.datetime.now(pytz.timezone('Europe/Moscow'))
    return {"hours": now.hour, "minutes": now.minute, "seconds": now.second}


@app.get("/", response_class=HTMLResponse)
async def show_moscow_time(request: Request):
    """Renders the Moscow time page."""
    time_data = get_moscow_time()
    return templates.TemplateResponse("index.html",
                                      {"request": request, **time_data})


# Prometheus metrics definitions
REQUEST_TIME = Summary(
    "request_processing_seconds",
    "Time spent processing request"
)

REQUEST_COUNT = Counter(
    "request_total",
    "Total number of requests"
)

@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )