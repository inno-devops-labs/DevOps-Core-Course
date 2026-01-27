## Framework Selection

I chose FastApi because it's simple, easy to create endpoints, and has automatic documentation.

| Framework   | Pros                                                  | Cons                                        | Reason Not Chosen                 |
|-------------| ----------------------------------------------------- | ------------------------------------------- | --------------------------------- |
| **FastAPI** | Async support, type safety, OpenAPI, high performance | Slight learning curve                       | **Chosen**                        |
| Flask       | Simple, minimal                                       | No async by default, no built-in validation | Less suitable for structured APIs |
| Django      | Full-featured, mature                                 | Heavy, overkill for small service           | Too complex for this task         |

## Best Practices Applied

1. Environment-based Configuration

    ```python
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    ```
    
    it important because it enables configuration without code changes.

2. Separation of Concerns

   ```python
      class HealthCheckService:
       async def get_info(self, request: Request) -> InfoResponse:
           ...
   
   ```
   
   it important because it easier testing, cleaner routing layer

3. Typed Responses with Pydantic

   ```python
   class InfoResponse(BaseModel):
       service: ServiceInfo
       system: SystemInfo
       runtime: RuntimeInfo
       request: RequestInfo
       endpoints: list[EndpointInfo]
   ```
   
   it important because guarantees response structure and improves readability

4. Logging

   ```python
   logger = logging.getLogger(__name__)
   logger.info("Handling info request")
   ```
   
   it important because it centralized observability and works seamlessly with Uvicorn

## API Documentation

1. GET `/` - get system information

   Response example:
   ```json
   {
     "service": {
       "name": "devops-info-service",
       "version": "1.0.0",
       "description": "DevOps course info service",
       "framework": "Fastapi"
     },
     "system": {
       "hostname": "Th1ef",
       "platform": "Windows",
       "platform_version": "10.0.26200",
       "architecture": "AMD64",
       "cpu_count": 8,
       "python_version": "3.13.5"
     },
     "runtime": {
       "uptime_seconds": 18,
       "uptime_human": "0 hours, 0 minutes",
       "current_time": "2026-01-26T12:41:50.413788Z",
       "timezone": "UTC"
     },
     "request": {
       "client_ip": "127.0.0.1",
       "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
       "method": "GET",
       "path": "/"
     },
     "endpoints": [
       {
         "path": "/",
         "method": "GET",
         "description": "Service information"
       },
       {
         "path": "/health",
         "method": "GET",
         "description": "Health check"
       }
     ]
   }
   ```

2. GET `/health` - get service status

   Response example:
   ```json
   {
     "status": "healthy",
     "timestamp": "2026-01-27T10:32:15.552053Z",
     "uptime_seconds": 7390
   }
   ```
   
3. Testing Commands

   Using curl:
   ```bash
   curl http://localhost:5000/
   curl http://localhost:5000/health
   ```
   
   or auto generated documentation:
   
   ```bash
   http://localhost:5000/docs
   ```
   
## Testing Evidence

- Successful responses from `/` and `/health`
- Correct JSON structure returned
- Terminal output from uvicorn confirming requests
- Screenshots Swagger UI

## Challenges & Solutions

There were no difficulties
