# Lab 01 — DevOps Info Service (Go)

## Implementation Details

The Go implementation keeps everything in a single `main.go` file using only the standard library. This is idiomatic for small Go services — no need for a framework.

**Key components:**
- Struct types with JSON tags for response serialization
- `rootHandler` and `healthHandler` for the two endpoints
- `getUptime()` and `getHostname()` helper functions
- `startTime` package-level variable for uptime tracking

## Key Differences from Python Version

| Aspect          | Python (FastAPI)           | Go (net/http)              |
|-----------------|----------------------------|----------------------------|
| Models          | Pydantic `BaseModel`       | Structs with JSON tags     |
| Routing         | `@router.get("/")`         | `http.HandleFunc("/", fn)` |
| JSON            | Automatic from dict/model  | `json.NewEncoder().Encode` |
| Server          | uvicorn (external)         | Built-in `http.ListenAndServe` |
| Dependencies    | fastapi, uvicorn           | None (stdlib only)         |
| Field naming    | `python_version`           | `go_version`               |

## Build & Run

```bash
go build -o devops-info-service
./devops-info-service
```

## Testing

```bash
curl http://localhost:8080/
curl http://localhost:8080/health
```

## Screenshots

Screenshots in `screenshots/`:
- Compilation and binary output
- Running application with endpoint responses
