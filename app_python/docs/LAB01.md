#### Selected Framework: FastAPI
I choose FastAPI as a framework because it is modern, fast, and customizable. Also, FastAPI has interaction with Pydantic for data validation.

#### Used Best Practices
- Used `.env` file to manage configuration settings
- Used Pydantic models to structure and validate response data
- Used descriptive names for functions and variables
- Used MVC Architecture to separate logic for maintainability and easy testing

### How to run service
1. Fill .env file (optional)
```env
HOST=localhost
PORT=5000
SERVICE_TITLE=devops-info-service
SERVICE_VERSION=1.0.0
SERVICE_DESCRIPTION=DevOps course info service
SERVICE_FRAMEWORK=FastAPI
```
3. Run virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```
4. Install dependencies
```bash
pip install -r requirements.txt
```
5.Run the service

### Service endpoints
```bash
python app.py
```
#### 1. Root endpoint
To test root endpoint run:
```bash
curl http://localhost:5000/
```
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "DESKTOP-1J70LO4",
    "platform": "Windows",
    "platform_version": "10.0.26100",
    "architecture": "AMD64",
    "cpu_count": 16,
    "python_version": "3.11.7"
  },
  "runtime": {
    "uptime_seconds": 10,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-01-28T18:59:11.516321",
    "timezone": "RTZ 2 (зима)"
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

#### 2. Health Check endpoint
To test health check endpoint run:
```bash
curl http://localhost:5000/health
```
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T18:59:28.764449",
  "uptime_seconds": 27
}
```
### Challenges & Solutions
- **Have single time_start for all endpoints**: Make file `runtime.py` to store `time_start` variable and import it in `app.py` to start counting uptime from the moment the application starts.
- **Big response for root endpoint**: Create separate Pydantic models for different parts of the response to keep code organized."

### GitHub Community
Starring the project helps developers and users understand that the project is useful. It can also increase the visibility of the project on GitHub which will attract more users and contributors.
Following the developers on GitHub help track modern trends. Also, employers will see that account is active and developer is interested in professional growth.