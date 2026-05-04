# LAB01 — Bonus Task (Go)

## Implemented Endpoints
- `GET /` — returns service, system, runtime, request info + endpoints list (JSON)
- `GET /health` — returns health status + timestamp + uptime_seconds (JSON)

The JSON structure matches the Python version (same top-level fields and same key layout inside each section).

## How to Run (from source)
```bash
go run .
```
#### Test:

```bash
curl -s http://127.0.0.1:8080/ | python -m json.tool curl -s http://127.0.0.1:8080/health | python -m json.tool
```

## How to Build and Run (binary)

#### Build:

```bash
go build -o devops-info-service ls -lh devops-info-service
```

#### Run:

```bash
./devops-info-service
```

#### Test binary:

```bash
curl -s http://127.0.0.1:8080/health | python -m json.tool
```

## Screenshots

Screenshots are stored in `docs/screenshots/`:

Recommended set:
- `01-go-run.png` — running from source (`go run .`)
- `02-main-endpoint.png` — `GET /` output
- `03-health-endpoint.png` — `GET /health` output
- `04-go-build.png` — `go build` + `ls -lh` showing binary size
- `05-binary-run.png` — running compiled binary (`./devops-info-service`)
- `06-binary-health.png` — health check from binary run