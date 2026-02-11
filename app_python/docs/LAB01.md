# Lab 01 — DevOps Info Service

## Framework Selection

**Choice:** FastAPI

| Criteria           | Flask          | FastAPI             | Django            |
|--------------------|----------------|---------------------|-------------------|
| Performance        | Moderate       | High (async)        | Moderate          |
| Auto documentation | No (manual)    | Yes (Swagger/ReDoc) | No                |
| Type safety        | No             | Yes (Pydantic)      | Partial           |
| Learning curve     | Low            | Low-Medium          | High              |
| Async support      | Limited        | Native              | Partial           |

**Why FastAPI:**
- Built-in request validation with Pydantic models
- Automatic OpenAPI/Swagger documentation at `/docs`
- Native async support for future scalability
- Type hints enforced at runtime, catching bugs early

## Best Practices Applied

1. **Clean code structure** — separated into `models/`, `routes/`, `services/`, and `config.py`. Each module has a single responsibility.
2. **Pydantic response models** — all endpoints use typed response schemas, ensuring consistent JSON output and enabling auto-generated API docs.
3. **Environment variable configuration** — `HOST`, `PORT`, `DEBUG` are configurable via env vars with sensible defaults.
4. **Error handling** — custom 404 and 500 handlers return structured JSON errors.
5. **Logging** — configured with timestamps and log levels for production readability.
6. **Pinned dependencies** — `requirements.txt` uses exact versions for reproducible builds.
7. **Proper `.gitignore`** — excludes `__pycache__/`, `venv/`, IDE files, and OS artifacts.

## API Documentation

### `GET /` — Service Information

```bash
curl http://localhost:8000/
```

Returns service metadata, system info, runtime uptime, request details, and available endpoints.

### `GET /health` — Health Check

```bash
curl http://localhost:8000/health
```

Returns health status, timestamp, and uptime in seconds.

### Error Responses

```bash
curl http://localhost:8000/nonexistent
# {"error": "Not Found", "message": "Endpoint does not exist"}
```

## Testing Evidence

Screenshots in `screenshots/`:
- `01-main-endpoint.png` — GET / response
- `02-health-check.png` — GET /health response
- `03-formatted-output.png` — Pretty-printed JSON output

## Challenges & Solutions

1. **Pyright not resolving imports** — The workspace root differs from `app_python/`, so basedpyright couldn't find the venv. Solved by adding `pyrightconfig.json` at the workspace root with `venvPath` pointing to `app_python`.
2. **Shared uptime logic** — Both `/` and `/health` need uptime data. Extracted `services/uptime.py` as a shared module with `START_TIME` initialized at import time.
3. **Type narrowing for TypedDict** — `get_uptime()` originally returned `dict[str, int | str]`, which pyright couldn't narrow. Fixed by using `TypedDict` for precise per-key types.

## GitHub Community

Starring repositories helps with discovery and bookmarking — it signals project quality to the community and encourages maintainers. Following developers builds professional connections and keeps you informed about relevant projects and industry trends.
