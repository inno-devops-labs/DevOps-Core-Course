"""
FastAPI application that displays the current time in Moscow timezone.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Moscow Time Display", version="1.0.0")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def get_moscow_time(request: Request):
    """
    Display the current time in Moscow timezone.

    Returns:
        HTMLResponse: Rendered HTML page with Moscow time
    """
    moscow_tz = ZoneInfo("Europe/Moscow")
    current_time = datetime.now(moscow_tz)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "time": current_time.strftime("%H:%M:%S"),
            "date": current_time.strftime("%B %d, %Y"),
            "timezone": "Moscow (MSK)"
        }
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns:
        dict: Status of the application
    """
    return {"status": "healthy", "service": "moscow-time-app"}
