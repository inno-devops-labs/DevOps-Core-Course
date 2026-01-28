# LAB01 — DevOps Info Service (Python)


## Framework Selection
**Chosen:** Flask

**Why Flask:** It is lightweight, simple for beginners, and perfect for a small JSON API.


### Comparison
| Framework | Pros | Cons |
|---|---|---|
| **Flask** | Minimal, easy routing, fast to implement | Less built-in features |
| FastAPI | Async-ready, auto docs (OpenAPI) | Slightly more concepts upfront |
| Django | Full-featured, ORM, admin panel | Overkill for small amount of endpoints |


## Best Practices Applied
1. **Clean structure & helpers**: logic split into small functions (`get_uptime_seconds`, `get_platform_version`, etc.).
2. **Configuration via env vars**: `HOST`, `PORT`, `DEBUG` read from environment.
3. **Error handling**: JSON error responses for `404` and `500`.
4. **Logging**: configured with `logging`; request method/path logged in `@before_request`.

Example (error handling):
```py
@app.errorhandler(404)
def not_found(_):
    return jsonify({"error":"Not Found","message":"Endpoint does not exist"}), 404
```


## API Documentation

### `GET /`

Returns:

* `service`: name, version, description, framework
* `system`: hostname, platform, platform_version, architecture, cpu_count, python_version
* `runtime`: uptime + timestamp + timezone
* `request`: client IP + user agent + method + path
* `endpoints`: list of endpoints

Test:

```bash
curl -s http://127.0.0.1:5000/ | python -m json.tool
```

### `GET /health`

Test:

```bash
curl -s http://127.0.0.1:5000/health | python -m json.tool
```

Expected shape:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-07T14:30:00.000Z",
  "uptime_seconds": 3600
}
```


## Testing evidence

In the directory app_python/docs/screenshots I provided three screenshots:
- Main endpoint showing complete JSON
- Health check response
- Formatted output


## Challenges & Solutions

**Challenge:** This was my first time using Flask, so I had to learn routing, request handling, and JSON responses.  
**Solution:** I kept the app minimal and used small helper functions for system/runtime info. I also added a client IP getter (checks `X-Forwarded-For`) and consistent UTC timestamps.

## GitHub Community

Starring useful repositories is a sign of appreciation and helps discovery in open source.
Following developers helps collaboration because you can see activity, learn patterns, and stay aligned on project progress.

