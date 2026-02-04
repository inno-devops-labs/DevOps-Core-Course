# LAB01 — DevOps Info Service (Python)

## Framework Selection
Chosen framework: **Flask**.

**Why Flask**
- Simple and lightweight for two endpoints
- Minimal boilerplate
- Easy to run locally without extra ASGI server

### Comparison (short)
| Framework | Pros | Cons |
|---|---|---|
| Flask | Simple, minimal | No built-in async, fewer auto docs |
| FastAPI | Auto OpenAPI docs, async | More concepts (ASGI, uvicorn), slightly more setup |
| Django | Full-stack | Overkill for this lab |

## Best Practices Applied
- Clear project structure and documentation
- Environment-based configuration: `HOST`, `PORT`, `DEBUG`
- Logging configured (debug logs enabled via `DEBUG=true`)
- Error handlers: 404 and 500
- UTC timestamps via `datetime.now(timezone.utc)`

## API Documentation

### GET /
Example:
```bash
curl -s http://127.0.0.1:5000/ | python -m json.tool
```

### GET /health
Example:
```bash
curl -s http://127.0.0.1:5000/health | python -m json.tool
```

## Testing Evidence (Screenshots)
Put your screenshots into:
- `docs/screenshots/01-main-endpoint.png`
- `docs/screenshots/02-health-check.png`
- `docs/screenshots/03-formatted-output.png`

## Challenges & Solutions
- (Write 2–4 lines: what was confusing and how you fixed it)

## GitHub Community
Starring repositories helps discover and bookmark useful projects and signals interest/support to maintainers.  
Following developers helps track activity, learn patterns, and makes collaboration in team projects easier.
