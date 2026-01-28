# Lab 1 Report: DevOps Info Service

## 1. Chosen Web Framework
 I chose **FastAPI** as the web framework for this lab because it allows me to focus on DevOps-related aspects of the course rather than spending time learning a new framework from scratch.

I already have some basic experience working with FastAPI from a frontend perspective, which helps me quickly build a stable and predictable API. This makes it possible to concentrate on core DevOps practices such as application configuration via environment variables, containerization, CI/CD pipelines, monitoring, and future deployment to Kubernetes.

From a technical perspective, FastAPI is well suited for production-oriented services. It provides asynchronous request handling, automatic OpenAPI documentation, and strong typing based on Python type hints, which improves code clarity, reliability, and maintainability. These features are especially valuable for services that will be extended and evolved throughout the course.

Compared to Flask, FastAPI offers built-in validation and API documentation with less manual configuration. Compared to Django, it is lighter and better suited for a small, API-focused service without unnecessary complexity.

## 2. Best Practices Applied
The following best practices were implemented to ensure the application is production-ready:

- **Logging and Observability**: Configured the standard `logging` module instead of `print()` statements. This allows for better tracking of application behavior in containerized environments.
  - *Example:* `logger.info(f"Root endpoint called by {request.client.host}")`
- **Environment Configuration**: Used `os.getenv` to manage settings like `HOST` and `PORT`. This ensures the app is portable across development, CI, and production environments.
  - *Example:* `PORT = int(os.getenv("PORT", 5000))`
- **Robust Error Handling**: Implemented a custom 404 handler and `try-except` blocks for the main logic. This ensures that the API returns valid JSON even when errors occur.
- **Clean Code & Documentation**: Followed PEP 8 for import grouping and used function docstrings. These docstrings are automatically used by FastAPI to populate the interactive API documentation.

## 3. API Documentation
The service exposes two primary endpoints.

### 3.1 Main Endpoint (`/`)
Returns comprehensive metadata about the service, system environment, and current request.
- **Request**: `curl -s http://localhost:5000/`
- **Response**: A JSON object containing `service`, `system`, `runtime`, and `request` details.

### 3.2 Health Check (`/health`)
A lightweight endpoint used for monitoring the application's availability, essential for future Kubernetes health probes.
- **Request**: `curl -s http://localhost:5000/health`
- **Response**: `{"status": "healthy", "timestamp": "...", "uptime_seconds": ...}`

## 4. Testing Evidence
To verify that the service works as expected, I used both the browser and command-line tools:

- Opened `http://127.0.0.1:5000/` in the browser to check the full JSON with `service`, `system`, `runtime`, `request`, and `endpoints`.
- Opened `http://127.0.0.1:5000/health` to confirm that the health check returns `status`, `timestamp` and `uptime_seconds`.
- Used `curl` together with `jq` to see formatted JSON responses in the terminal:

```bash
curl -s http://127.0.0.1:5000/ | jq
curl -s http://127.0.0.1:5000/health | jq
```

Screenshots are saved in `app_python/docs/screenshots/` and show:
- **Screenshot 1**: Main endpoint in the browser showing the full JSON structure.  
![1](/Users/marinalavrova/Documents/Projects/study_projects/DevOps-Core-Course/app_python/docs/screenshots/01-main-endpoint.png)
- **Screenshot 2**: Health check response confirming the "healthy" status.  
![2](/Users/marinalavrova/Documents/Projects/study_projects/DevOps-Core-Course/app_python/docs/screenshots/02-health-check.png)
- **Screenshot 3**: Terminal output using `jq` to show formatted/pretty-printed JSON.  
![3](/Users/marinalavrova/Documents/Projects/study_projects/DevOps-Core-Course/app_python/docs/screenshots/03-formatted-output.png)
## 5. Challenges & Solutions
During the lab I encountered several small issues and used them to better understand FastAPI and the runtime environment:

1. **Installing and running uvicorn**  
   Initially the `uvicorn` command was not available. I solved this by creating a virtual environment (`python -m venv venv`), activating it, and installing `fastapi` and `uvicorn[standard]` via `requirements.txt`.

2. **Accessing request information in the `/` endpoint**  
   At first I tried to use `request` inside the handler without declaring it as a parameter, which caused a `NameError`. The fix was to import `Request` from FastAPI and accept it as an argument: `def read_root(request: Request)`. This also helped me understand how FastAPI injects the request object.

3. **Understanding HOST, PORT and 0.0.0.0**  
   It was not obvious why the server binds to `0.0.0.0` while I still access it via `localhost`. After some experiments I learned that `0.0.0.0` means “listen on all interfaces”, and clients connect using `127.0.0.1` locally or my local network IP address.

## 6. GitHub Community
Starring repositories is crucial in the open-source ecosystem as it bookmarks high-quality projects, signals community trust, and helps maintainers gain visibility for their work. Following fellow developers and mentors facilitates professional growth by allowing you to observe industry-standard coding practices and stay updated on the latest technical trends.


