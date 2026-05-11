import platform
import os
import socket
from fastapi import FastAPI, Request
from datetime import datetime, timezone

#------------------Fonctions---------------------------------
start_time = datetime.now()

def getSystemInformation():
    hostname = socket.gethostname()
    plaform_version = platform.version()
    platform_name = platform.system()
    architecture = platform.machine()
    python_version = platform.python_version()
    cpu_count = os.cpu_count()
    
    return {
            "hostname": hostname,
            "platform": platform_name,
            "platform_version": plaform_version,
            "architecture": architecture,
            "cpu_count": cpu_count,
            "python_version": python_version
            }

def getService():
    return {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask"
            }

def get_uptime():
    delta = datetime.now() - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }

def getRuntime():
    delta = datetime.now() - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    # la timezone
    time_now = datetime.now()
    local_now = time_now.astimezone()
    local_tz = local_now.tzinfo
    local_tzname = local_tz.tzname(local_now)

    return {
        "uptime_seconds": seconds,
        "uptime_human": f"{hours} hours, {minutes} minutes",
        "current_time": time_now,
        "timezone": local_tzname
    }

def getRequestInfo(request: Request):
    return {
            "client_ip": request.client.host,
            "user_agent": request.headers.get('user-agent'),
            "method": request.method,
            "path": request.url.path
            }



#--------------------app----------------------------------------
app = FastAPI()


@app.get("/")
def read_root(request:Request):
    return {
            "service": getService(),
            "system": getSystemInformation(),
            "runtime": getRuntime(),
            "request": getRequestInfo(request),
            "endpoints": [
                {"path": "/", "method": "GET", "description": "Service information"},
                {"path": "/health", "method": "GET", "description": "Health check"}
                ]
            }

@app.get("/health")
def read_health():
    return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': get_uptime()['seconds']
    }
 
