# DevOps Info Service (Go)

Go implementation of the DevOps Info Service for the **DevOps Core Course**.
This project includes:
- Lab 1 bonus (Go implementation)
- Lab 2 bonus (multi-stage Docker image)

## Features
- `GET /` — JSON with service metadata, system info, runtime info, request info, and available endpoints
- `GET /health` — JSON health check with uptime
- JSON structure matches the Python version (course requirement)
- Multi-stage Docker build for small runtime image

## Local Run
### Prerequisites
- Go 1.20+

### Run
```bash
cd app_go
go run .
```

### Test
```bash
curl -s http://localhost:8080/ | head
curl -s http://localhost:8080/health
curl -i http://localhost:8080/does-not-exist
```

## Docker (Lab 2 Bonus)
### Build final image
```bash
cd app_go
docker build -t devops-info-go:lab02 .
```

### Build builder stage (size comparison)
```bash
docker build --target builder -t devops-info-go:builder .
docker images | grep devops-info-go
```

### Run
```bash
docker run --rm -p 8080:8080 devops-info-go:lab02
```

## Screenshots / Evidence
All screenshots are located here:
- `app_go/docs/screenshots/`

Lab 2 bonus evidence:
- Curl tests: `docs/screenshots/curl_to_custom_image.png`
- Builder vs final image sizes + successful run: `docs/screenshots/image_size_compare_with_successful_starting.png`
