# Lab 1 — Bonus (Go Implementation)

## Framework Selection
- **Choice:** Go `net/http`
- **Why:** Zero external deps, fast startup, produces single binary, easy to containerize, idiomatic stdlib routing is enough for two endpoints.
- **Comparison:**
  - Flask/FastAPI (Python): great DX but need interpreter, slower cold start.
  - Echo/Gin (Go): more features but unnecessary for two simple routes; stdlib keeps footprint minimal.

## Best Practices Applied
- **Config via env:** `HOST`/`PORT` with sensible defaults.
- **Structured types:** Separate structs for service/system/runtime/request/endpoint to keep responses organized.
- **Logging middleware:** Basic request log with latency and client IP.
- **Error handling:** JSON writer reports encoding errors; hostname/OS version fall back to `"unknown"` safely.
- **Pretty JSON:** Indented output improves readability for grading/screenshots.

## API Documentation
- `GET /`  
  - Returns service metadata, system info (hostname, OS, arch, CPU, Go version, platform version), runtime (uptime seconds/human, current time UTC, timezone), request info (client IP, user agent, method, path), and available endpoints.
  - Example: `curl -s http://localhost:8080/ | jq .`
- `GET /health`  
  - Returns status `healthy`, current UTC timestamp, and uptime seconds.  
  - Example: `curl -s http://localhost:8080/health | jq .`

## Testing Commands
```bash
cd app_go
go run main.go
curl -s http://localhost:8080/ | jq .
curl -s http://localhost:8080/health | jq .
```

## Challenges & Solutions
- **No Go toolchain on host:** Could not run `go mod init`; created `go.mod` manually and documented requirement to install Go for execution.
- **OS version discovery:** Used best-effort parse of `/etc/os-release` to populate `platform_version`; falls back to `"unknown"` if unavailable.

## Screenshots
Placed in `docs/screenshots/`:

- [go-main](/app_go/docs/screenshots/go-main.jpg)
- [go-health](/app_go/docs/screenshots/go-health.jpg)
- [go-started](/app_go/docs/screenshots/go-started.jpg)
