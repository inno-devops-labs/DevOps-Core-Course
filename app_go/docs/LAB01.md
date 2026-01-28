# LAB01 — DevOps Info Service (Go Bonus)

## Language Selection
**Chosen:** Go

## Best Practices Applied
1. **Clean structure**: small helper functions (`uptimeSeconds`, `clientIP`, `platformVersion`).
2. **Configuration via env vars**: `HOST`, `PORT`, `DEBUG` read from environment.
3. **Basic error handling**: unknown routes return JSON 404 (`notFound`).
4. **Logging**: a simple middleware logs request method and path.

Example (logging middleware):
```go
func loggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        log.Printf("Request: %s %s", r.Method, r.URL.Path)
        next.ServeHTTP(w, r)
    })
}
```

## API Documentation

### `GET /`

Returns the same JSON structure as the Python version:

* `service`, `system`, `runtime`, `request`, `endpoints`

Test:

```bash
curl -s http://127.0.0.1:8080/ | python -m json.tool
```

### `GET /health`

Test:

```bash
curl -s http://127.0.0.1:8080/health | python -m json.tool
```

## Build & Run

Build:

```bash
go build -o devops-info-service .
```

Run:

```bash
./devops-info-service
```


## Testing Evidence
In the directory go_python/docs/screenshots I provided three screenshots:

* `01-main-endpoint.png` — `GET /` response
* `02-health-check.png` — `GET /health` response
* `03-binary-size.png` — `ls -lh devops-info-service`

## Challenges & Solutions

**Challenge:** Mapping the exact JSON structure and formatting timestamps consistently.  
**Solution:** I created clear response structs, returned JSON with `encoding/json`, and used UTC timestamps (`time.Now().UTC()`).

## Binary Size Comparison (Go vs Python)

Go compiles into one executable, so we can measure it directly. Python is not a single binary, so we compare its source folder size (without `venv`) as a simple footprint estimate.

### Results

Go binary:

```bash
ls -lh devops-info-service
```

* Size: **7.5M**

Python project (without venv):

```bash
du -sh . --exclude=venv --exclude=__pycache__
```

* Size: **100K**
