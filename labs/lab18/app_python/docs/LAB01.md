# Lab 1

## 1) Framework Selection
**Chosen framework:** FastAPI

**Why FastAPI:**
- Modern, async-ready, OpenAPI-compliant
- Great docs and async support make it production-ready
- Compared to Flask, it comes with more built-in features

| Framework | Pros | Cons |
|---|---|---|
| Flask | Simple, lightweight, easy learning curve | Less "built-in" features than FastAPI |
| FastAPI | Modern, async-ready, OpenAPI-compliant | Slightly more concepts (typing, ASGI) |
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
- Basic logging configured on INFO level on program start, `/` and `/health` endpoints

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
- `main-endpoint.png` — main endpoint JSON output
- `health.png` — health endpoint JSON output

## 5) Challenges & Solutions

- **Challenge:** Complex JSON structure requirement
- **Solution:** Implemented endpoints step-by-step and validated output using curl + json.tool.
- **Challenge:** Use of environment variables
- **Solution:** Clear examples helped to reveal

## 6) GitHub Community

Starring a repository is a way to bookmark a project of interest, show appreciation to its maintainers, and contribute to its visibility in the GitHub ecosystem. 
Following developers, including the professor, TAs, and classmates, allows for networking, easier access to their work, and the potential for collaboration in future projects.
