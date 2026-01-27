# Lab 1

## 1) Framework Selection
**Chosen framework:** Flask

**Why Flask:**
- Minimal setup and easy to understand for a beginner
- Perfect for a small service with only a couple endpoints
- Clear request handling and simple JSON responses

| Framework | Pros | Cons |
|---|---|---|
| Flask | Simple, lightweight, easy learning curve | Less “built-in” features than Django |
| FastAPI | Great docs, async-ready, OpenAPI | Slightly more concepts (typing, ASGI) |
| Django | Full-featured framework | Overkill for this small service |

## 2) Best Practices Applied
### Clean Code Organization
- Separate helper functions: system info, request info, uptime
- Clear naming and small functions

### Configuration via Environment Variables
- `HOST`, `PORT`, `DEBUG` are read from environment variables

### Error Handling
- Custom JSON responses for 404 and 500 errors

### Logging
- Basic logging configured (INFO level)
- Logs requests to `/` and `/health`

## 3) API Documentation
### GET /
Returns service metadata, system information, runtime info and request details.

Example test:
```bash
curl -s http://127.0.0.1:5000/ | python -m json.tool
```
### GET /health

Returns health status, timestamp and uptime.

Example test:

`curl -s http://127.0.0.1:5000/health | python -m json.tool`

## 4) Testing Evidence

Screenshots are stored in:  
`docs/screenshots/`
- `main-endpoint.png` — main endpoint JSON output
- `health-check.png` — health endpoint JSON output

## 5) Challenges & Solutions

- **Challenge:** Understanding required JSON structure  
    **Solution:** Implemented endpoints step-by-step and validated output using curl + json.tool.
- **Challenge:** Making the service configurable  
    **Solution:** Added environment variables `HOST` and `PORT` and verified by running on port 8080.

## 6) GitHub Community

Starring repositories helps bookmark useful projects and signals appreciation to maintainers, improving open-source discovery.  
Following developers (professor/TAs/classmates) helps networking and makes it easier to learn from others’ activity and collaborate in team projects.