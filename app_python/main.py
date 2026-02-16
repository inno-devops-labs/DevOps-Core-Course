import datetime as dt
import pytz
import os
import time
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from prometheus_client import Summary, Counter, generate_latest, CONTENT_TYPE_LATEST

# Initialize FastAPI app
app = FastAPI()

# Set up Jinja2 for rendering templates
templates = Jinja2Templates(directory="templates")

VISITS_DIR = os.getenv("VISITS_DIR", "./data")
VISITS_FILE = os.path.join(VISITS_DIR, "visits.txt")

os.makedirs(VISITS_DIR, exist_ok=True)

if not os.path.exists(VISITS_FILE):
    with open(VISITS_FILE, "w") as f:
        f.write("0")

def get_moscow_time():
    """Returns the current time in Moscow as a dictionary."""
    now = dt.datetime.now(pytz.timezone('Europe/Moscow'))
    return {"hours": now.hour, "minutes": now.minute, "seconds": now.second}

def read_visits():
    """Read the current visit count from the file."""
    with open(VISITS_FILE, "r") as f:
        return int(f.read().strip())

def increment_visits():
    """Increment the visit count in the file."""
    visits = read_visits() + 1
    with open(VISITS_FILE, "w") as f:
        f.write(str(visits))
    return visits    

@app.get("/", response_class=HTMLResponse)
async def show_moscow_time(request: Request):
    """Renders the Moscow time page."""
    time_data = get_moscow_time()
    visits_count = increment_visits() 
    return templates.TemplateResponse("index.html",
                                      {"request": request, **time_data})


    
@app.get("/visits", response_class=PlainTextResponse)
def visits():
    """Return the total number of visits."""
    return str(read_visits())
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