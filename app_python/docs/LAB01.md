# Lab 1 — DevOps Info Service (Python)

## Framework Selection
- **Choice:** Flask 3.1.0 — lightweight, familiar routing, simple JSON responses. Suits well for person not familliar with python backend developing.

| Framework | Pros | Cons |
|-----------|------|------|
| Flask | Minimal, quick startup, large ecosystem | Async support limited compared to FastAPI |
| FastAPI | Automatic docs, async-native | Slightly heavier, needs uvicorn |
| Django | Batteries included, ORM | Overkill for two endpoints |

## Best Practices Applied
- Logging configured at startup; request logging via `before_request`.
- JSON error handlers for 404/500 to keep API consistent.
- Environment-based config (`HOST`, `PORT`, `DEBUG`) for portability.
- Small, pure functions (`get_system_info`, `get_uptime`) to simplify testing.

## API Documentation
- `GET /` — returns service metadata, system info, runtime (uptime, time, timezone), request info, endpoint catalog.
- `GET /health` — returns status `healthy`, current timestamp (UTC ISO8601), and uptime seconds.

### Example Commands
```bash
curl -s http://localhost:8080/ | jq
curl -s http://localhost:8080/health | jq
```

## Testing Evidence
Screenshots saved under `docs/screenshots/`:
- `01-main-endpoint.png`
- `02-health-check.png`
- `03-formatted-output.png`

## Challenges & Solutions
- Placeholder: document any runtime or environment issues encountered.

## GitHub Community
- Starring repositories surfaces useful tools and signals interest to maintainers.
- Following developers keeps you aware of their activity, aiding collaboration and professional growth.
