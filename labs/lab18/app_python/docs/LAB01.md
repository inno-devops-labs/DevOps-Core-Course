# Documentation

## Framework Selection

I chose Flask because it is quite good for the small projects and easy enough for the beginners, as I didn't have an experience with API before. It also has a lot of community support since it was released long ago.

| Framework | Features |
|---------|------------|
| Flask | Easy to learn, a lot of documentation |
| FastAPI | Harder to learn, more suitable for big projects (but from reddit comments people seem to like it a lot)|
| Django | Also too heavy for a small project |

## Best Practices Applied

- Informative comments

```python
# decorator for / path
# decorator for /health path
# error handling
```
- PEP8 standarts with auto linting from black formatter (example is app.py itself)

- clear structure 

- error handling

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    return (
        jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
            }
        ),
        500,
    )
```

- logging
```python
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger.info("Application starting...")

logger.debug(f"Request: {request.method} {request.path}") # inside decorators
```
- requirements.txt and .gitignore

## API Documentation

- The web app can be accesed by this link: http://127.0.0.1:5000

### Request/response examples

- Request Examples:
    - GET / HTTP/1.1
    - GET /health HTTP/1.1
- Response examples
    - json and 200 OK code
    - {"error":"Not Found","message":"Endpoint does not exist"} 404 not found error
    - {"error":"Internal Server Error","message":"An unexpected error occurred"} 500 internal server error

### Testing commands

- test urls
    - http://127.0.0.1:5000
    - http://127.0.0.1:5000/health
    - http://127.0.0.1:5000/unknown
- curl 
    - curl http://127.0.0.1:5000/unknown
    - curl http://127.0.0.1:5000/health
    - curl http://127.0.0.1:5000/

## Testing Evidence

### Screenshots

Screenshots can be found in app/python/docs/screenshots.

### Terminal output

#### Curl

```bash
fountainer@Veronicas-MacBook-Air DevOps-Core-Course % curl http://127.0.0.1:5000/unknown
{"error":"Not Found","message":"Endpoint does not exist"}

fountainer@Veronicas-MacBook-Air DevOps-Core-Course % curl http://127.0.0.1:5000/health 
{"status":"healthy","timestamp":"2026-01-28T22:32:13.607128","uptime_seconds":352}

fountainer@Veronicas-MacBook-Air DevOps-Core-Course % curl http://127.0.0.1:5000/      
{"message":{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"127.0.0.1","method":"GET","path":"/","port":5000,"user_agent":"curl/7.81.0"},"runtime":{"current_time":"2026-01-07T14:30:00.000Z","timezone":"UTC","uptime_human":"1 hour, 0 minutes","uptime_seconds":{"human":"0 hours, 0 minutes","seconds":0}},"service":{"debug status":true,"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"arm64","cpu_count":8,"hostname":"Veronicas-MacBook-Air.local","platform":"Darwin","platform_version":"Ubuntu 24.04","python_version":"3.12.9"}}}
```
#### App started

```bash
devops) fountainer@Veronicas-MacBook-Air app_python % python app.py
2026-01-28 22:36:05,289 - __main__ - INFO - Application starting...
 * Serving Flask app 'app'
 * Debug mode: off
2026-01-28 22:36:05,299 - werkzeug - INFO - WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
2026-01-28 22:36:05,299 - werkzeug - INFO - Press CTRL+C to quit
2026-01-28 22:36:09,089 - werkzeug - INFO - 127.0.0.1 - - [28/Jan/2026 22:36:09] "GET /unknown HTTP/1.1" 404 -
2026-01-28 22:36:12,152 - __main__ - DEBUG - Request: GET /
2026-01-28 22:36:12,153 - werkzeug - INFO - 127.0.0.1 - - [28/Jan/2026 22:36:12] "GET / HTTP/1.1" 200 -
2026-01-28 22:36:18,600 - __main__ - DEBUG - Request: GET /health
2026-01-28 22:36:18,607 - werkzeug - INFO - 127.0.0.1 - - [28/Jan/2026 22:36:18] "GET /health HTTP/1.1" 200 -
2026-01-28 22:36:20,246 - __main__ - DEBUG - Request: GET /health
2026-01-28 22:36:20,247 - werkzeug - INFO - 127.0.0.1 - - [28/Jan/2026 22:36:20] "GET /health HTTP/1.1" 200 -
```

## Challenges & Solutions

- It was quite hard for me to understand the structure since I didn't work with Flask and API in general before. I got some info from stackoverflow, documentations, etc.

- I have encountered a problem with a jsonify library since I thought it wasn't comming from Flask library. Terminal errors helped to understand it eventually.

- It took some time to understand how methods from request library work. 

## GitHub Community

- starring repositories support open-source development and small but promising projects
- following developers lead to the opportunities of communication, exchanging experience, and making connections in the field.
