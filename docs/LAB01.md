# DevOps Course Lab 1

## Framework selection

I've chosen FastAPI because I'm most familiar with it, so it will be easier to work with it.

### Alternatives comparison

| Framework | Pros                               | Cons                                       |
| --------- | ---------------------------------- | ------------------------------------------ |
| FastAPI   | Async-ready, auto docs, type hints | Slightly more concepts than Flask          |
| Flask     | Very simple, huge ecosystem        | No built-in OpenAPI, more manual structure |
| Django    | Full-featured                      | Too heavy for a small info service         |

## Best practices applied

### Clean code organization

- Separate helper functions: `get_system_info()`, `get_uptime()`, `iso_utc_now()`.
- PEP 8 naming and import grouping.

### Error handling

- Custom handler for 404 returning JSON: `{"error":"Not Found","message":"Endpoint does not exist"}`.
- Global handler for 500 returning JSON + logs the exception.

### Logging

- Logs each request method/path via middleware.
- Uses `DEBUG` env var to switch log level and uvicorn reload.

### Dependencies

- `fastapi==0.115.0`
- `uvicorn[standard]==0.32.0`

### Git ignore

- venv, caches, IDE files, logs.

## API documentation

### GET /

Example:

```bash
curl -s http://127.0.0.1:5000/ | jq
```

### GET /health

Example:

```bash
curl -s http://127.0.0.1:5000/health | jq
```

## Testing evidence

### Output from CMD

![01](screenshots/lab01/lab1_01_cmd_output.png)

### Endpoints display on localhost/docs

![02](screenshots/lab01/lab1_02_fastapi_docs_endpoints.png)

### Output of Endpoints

![03](screenshots/lab01/lab1_03_fastapi_endpoints_showcase.png)

## GitHub Community

- Starring repositories helps discover and signal useful projects, which increases visibility and encourages maintainers.
- Following developers (professor/TAs/classmates) improves collaboration by making it easier to track work, learn practices, and build professional connections.
