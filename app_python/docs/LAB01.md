# Lab 1 Submission

## Framework Selection

**FastAPI** - Modern, fast, has auto-docs and async support.

| Criteria  | FastAPI   | Flask      | Django |
| --------- | --------- | ---------- | ------ |
| Speed     | Very Fast | Fast       | Medium |
| Auto Docs | Yes       | No         | No     |
| Async     | Yes       | Limited    | Yes    |
| Size      | Small     | Very Small | Large  |

**Why not Flask?** Flask is simpler but FastAPI has better async and auto-docs.

**Why not Django?** Too big for this simple service.

## Best Practices Applied

1. **Code Organization** - Separated into routes/, services/, config.py
2. **Error Handling** - 404 and 500 handlers
3. **Logging** - Basic logging setup
4. **Environment Variables** - Config via env vars
5. **Clear Function Names** - get_system_info(), get_uptime(), etc.

## API Documentation

### `GET /`

Returns service info, system info, runtime, request details, and endpoints list.

```bash
curl http://localhost:5000/
```

### `GET /health`

Returns health status and uptime.

```bash
curl http://localhost:5000/health
```

### Error Responses

```bash
curl http://localhost:5000/something
# {"error": "Not Found", "message": "Endpoint does not exist"}
```

## Testing Evidence

Screenshots in `docs/screenshots/`:

- `01-main-endpoint.png`
- `02-health-check.png`
- `03-formatted-output.png`

## Challenges & Solutions

1. **Function name conflict** — Named the route handler `get_system_info()` which conflicted with the imported function from `services.system_info`. When calling `get_system_info()` inside the route handler, Python was calling the route handler itself instead of the imported function, causing recursion errors. Fixed by importing the entire module as `import services.system_info as system_info_service` and accessing functions via `system_info_service.get_system_info()`.

2. **Timezone method call error** — Used `timezone.utc.tzname()` without arguments, but `tzname()` method requires a datetime object as parameter. This caused `TypeError: timezone.tzname() takes exactly one argument (0 given)`. Fixed by calling `tzname()` on a datetime object: `datetime.now(timezone.utc).tzname()`.

## GitHub Community

\*Starring repositories helps with discovery and bookmarking — it signals project quality to the community and encourages maintainers. Following developers builds professional connections and keeps you informed about relevant projects and industry trends.
