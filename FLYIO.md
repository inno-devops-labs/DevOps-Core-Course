# Lab 17 — Fly.io Edge Deployment

## 1. Application

The deployed application is the existing FastAPI DevOps Info Service from `app_python/`.

Important files:

```text
app_python/
├── app.py
├── config.py
├── Dockerfile
├── requirements.txt
└── fly.toml
```

The application exposes:

| Endpoint | Purpose |
|----------|---------|
| `/` | System information response |
| `/health` | Health check endpoint |
| `/metrics` | Prometheus metrics |

The Docker container exposes port `8000`, therefore Fly.io is configured with `internal_port = 8000`.

## 2. Fly.io Configuration

Configuration file: `app_python/fly.toml`

```toml
app = "devops-info-service-roma3213"
primary_region = "ams"

[build]
  dockerfile = "Dockerfile"

[env]
  HOST = "0.0.0.0"
  PORT = "8000"
  APP_ENV = "production"
  VISITS_FILE = "/tmp/visits"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[checks]
  [checks.health]
    type = "http"
    port = 8000
    path = "/health"
    interval = "10s"
    timeout = "2s"
    grace_period = "30s"
```

`VISITS_FILE` is set to `/tmp/visits` for Fly.io because the container runs as a non-root user and the app should not try to create `/data` unless a Fly Volume is attached.

## 3. Deployment Commands

```bash
cd app_python

fly auth login
fly auth whoami

fly launch --copy-config --no-deploy
fly deploy

fly status
fly logs
fly open
```

After deployment, the app URL should have this format:

```text
https://devops-info-service-roma3213.fly.dev
```

Health check verification:

```bash
curl https://devops-info-service-roma3213.fly.dev/health
```

## 4. Multi-Region Deployment

The primary region is Amsterdam:

```toml
primary_region = "ams"
```

Additional regions for the lab:

```bash
fly regions add iad sin
fly regions list
fly machines list
fly status
```

Selected regions:

| Region | Location |
|--------|----------|
| `ams` | Amsterdam |
| `iad` | Virginia, USA |
| `sin` | Singapore |

## 5. Secrets and Persistence

Secrets are managed by Fly.io and are exposed to the application as environment variables:

```bash
fly secrets set API_KEY="lab17-demo-key"
fly secrets set APP_MODE="flyio"
fly secrets list
```

For the minimal deployment, the visits counter is stored in `/tmp/visits`, so it is machine-local and can be reset after restarts. For persistent storage, a Fly Volume can be created:

```bash
fly volumes create app_data --size 1 --region ams
```

Then update `fly.toml`:

```toml
[env]
  VISITS_FILE = "/data/visits"

[[mounts]]
  source = "app_data"
  destination = "/data"
```

The basic deployment works without a volume, but the optional volume demonstrates persistence.

## 6. Monitoring and Operations

Useful operational commands:

```bash
fly dashboard
fly status
fly logs
fly releases
fly checks list
fly machines list
```

The Fly.io dashboard should be used to capture screenshots of:

- application overview;
- running machines;
- metrics page;
- health check status.

Screenshot folder prepared for this lab:

```text
app_python/docs/screenshots/lab17/
├── 01-fly-app-overview.png
├── 02-fly-machines-regions.png
├── 03-fly-metrics.png
└── 04-health-check.png
```

## 7. Kubernetes vs Fly.io

| Aspect | Kubernetes | Fly.io |
|--------|------------|--------|
| Setup complexity | Requires cluster, manifests, services, ingress and monitoring setup | Requires account, CLI and `fly.toml` |
| Deployment speed | Slower initial setup, flexible after that | Fast initial deployment with `fly deploy` |
| Global distribution | Manual multi-region setup | Built into the platform through regions |
| Cost for small apps | Usually higher because cluster resources must run | Lower for small apps because machines can auto-stop |
| Learning curve | Higher | Lower |
| Control/flexibility | Very high | Medium |
| Best use case | Complex systems, many services, custom infrastructure | Small or medium apps that need simple global deployment |

## 8. Summary

Fly.io is simpler than Kubernetes for this application because the service is a single containerized FastAPI app. Kubernetes gives more control, but for this lab Fly.io needs less infrastructure code and provides global deployment through regions.

This submission includes a ready Fly.io configuration. To complete the lab fully, run the deployment commands, add real screenshots, and replace the URL section with the actual deployed app URL if Fly assigns a different app name.
