# Lab 17 - Fly.io Edge Deployment

Run date: April 15, 2026

Resource-saving note:
I did not authenticate to Fly.io or create a live deployment in this session. Instead, I prepared a production-oriented `fly.toml`, updated the app so a real Fly deployment can verify region placement and secret injection, and documented the exact commands to run against a Fly account.

## Files Added

- `app_python/fly.toml`
- `FLYIO.md`

Files updated:

- `app_python/app.py`
- `app_python/tests/test_app.py`
- `app_python/README.md`

## Local Validation

Validation commands:

```text
py -3 -m flake8 app_python/app.py app_python/tests/test_app.py
py -3 -m pytest app_python/tests/test_app.py -q
py -3 -c "import pathlib, tomllib; tomllib.loads(pathlib.Path('app_python/fly.toml').read_text(encoding='utf-8')); print('fly-toml-ok')"
```

What was validated locally:

- the application test suite still passes after adding Fly-aware configuration reporting
- `fly.toml` is valid TOML syntax
- the app already exposes `/health` and `/metrics`, which Fly can use for checks and monitoring

## Fly.io Platform Concepts

### Fly Machines

- Fly Machines are lightweight VMs that run the app close to users
- they replace direct Kubernetes node and deployment management with a platform-managed machine model
- each machine still runs the app container image, so the Docker workflow from earlier labs remains useful

### Fly Volumes

- Fly Volumes provide persistent storage for stateful application data
- volumes are attached per machine and live in a single region
- that matters for the visits counter because the app stores its file under `/data/visits`

### Regions and Edge Deployment

- Fly routes users to nearby regions when machines are available there
- for this lab, the prepared multi-region example uses `ams`, `iad`, and `sin`
- the app now falls back to `FLY_REGION` when `APP_REGION` is not set, so the response can show the real region of the machine serving the request

## Prepared Fly Configuration

Checked-in config: `app_python/fly.toml`

Key settings:

```toml
app = "ravwvil-devops-info-service-fly"
primary_region = "ams"

[http_service]
  internal_port = 8000
  force_https = true

[checks.health]
  type = "http"
  port = 8000
  path = "/health"

[metrics]
  port = 8000
  path = "/metrics"

[[mounts]]
  source = "visits_data"
  destination = "/data"
```

Why these settings match the app:

- the container already serves HTTP on port `8000`
- `/health` returns a lightweight 200 response suitable for Fly checks
- `/metrics` exposes Prometheus metrics from the app
- `VISITS_FILE=/data/visits` makes the persistent counter survive restarts and redeployments when a Fly Volume is attached

## Deployment Workflow

### 1. Install and authenticate `flyctl`

Windows PowerShell install command:

```powershell
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
fly auth login
fly auth whoami
```

### 2. Launch using the prepared config

```powershell
cd .\app_python
fly launch --copy-config --no-deploy
```

Notes:

- if the configured app name is already taken, edit the `app` value in `fly.toml`
- keep `internal_port = 8000` because the container image listens on that port

### 3. Create persistence and secrets

```powershell
fly volumes create visits_data --size 1 --region ams
fly secrets set APP_USERNAME="fly-user" APP_PASSWORD="fly-password"
```

Why these two secrets were selected:

- the app now reports whether `APP_USERNAME` and `APP_PASSWORD` exist
- the response only shows boolean presence, not secret values

Prepared runtime verification:

```powershell
fly deploy
fly status
fly logs
curl https://ravwvil-devops-info-service-fly.fly.dev/
curl https://ravwvil-devops-info-service-fly.fly.dev/visits
```

Fields to verify in the root response:

- `configuration.platform.provider` should be `fly.io`
- `configuration.platform.fly_region` should show the region code of the serving machine
- `configuration.secrets.APP_USERNAME` should be `true`
- `configuration.secrets.APP_PASSWORD` should be `true`

## Multi-Region Deployment

Prepared regions:

- `ams` - primary region
- `iad` - secondary region
- `sin` - secondary region

Prepared commands:

```powershell
fly scale count 3 --region ams,iad,sin --max-per-region 1
fly regions list
fly scale show
fly machines list
```

Important persistence caveat:

- Fly documents that a volume exists in one region and attaches to one machine only
- if you want one machine in each region and two in the primary region, prepare one volume per machine

Example volume plan for four stateful machines:

```powershell
fly volumes create visits_data --size 1 --region ams
fly volumes create visits_data --size 1 --region ams
fly volumes create visits_data --size 1 --region iad
fly volumes create visits_data --size 1 --region sin
```

Prepared scaling commands:

```powershell
fly scale count 3 --region ams,iad,sin --max-per-region 1
fly scale count 2 --region ams
fly scale show
fly status
fly machines list
```

How to test distribution:

- reload the root URL several times and watch `configuration.platform.fly_region`
- compare machine placement in `fly machines list`
- use `fly ping` and `fly status` to inspect the nearest regions and machine health

## Monitoring and Operations

Prepared operational commands:

```powershell
fly status
fly logs
fly checks list
fly releases
fly dashboard
```

Operational expectations:

- `/health` backs the configured top-level Fly health check
- Fly documents that top-level checks are independent of request routing; if routing should depend on health, move the same probe into service-level checks later
- `/metrics` can be scraped through the Fly metrics configuration
- `fly releases` gives deployment history for rollbacks and change tracking

## Deployment Summary

Prepared deployment target:

- app config name: `ravwvil-devops-info-service-fly`
- expected public hostname after successful deploy: `https://ravwvil-devops-info-service-fly.fly.dev`
- prepared regions: `ams`, `iad`, `sin`
- persistence path: `/data/visits`
- monitored endpoints: `/health`, `/metrics`

Because no authenticated Fly account was used in this session, I did not record a real URL, release ID, machine IDs, or dashboard screenshots.

## Screenshots To Capture In A Live Run

When running this against a real Fly account, capture:

- Fly dashboard overview for the app
- Machines view showing multiple regions
- Metrics view showing CPU, memory, and network
- `fly status` output after deployment

## Kubernetes vs Fly.io

| Aspect | Kubernetes | Fly.io |
|--------|------------|--------|
| Setup complexity | Higher, because you manage cluster primitives and add-ons | Lower, because the platform handles most infrastructure concerns |
| Deployment speed | Slower initial setup, strong repeatability after that | Faster for a single app or small service |
| Global distribution | Powerful but requires explicit cluster and ingress design | Built in around regional machine placement |
| Cost for small apps | Often heavier operational overhead | Usually easier to justify for a small edge app |
| Learning curve | Steeper, especially around networking and storage | Gentler for simple web deployments |
| Control and flexibility | Highest level of control | Good defaults, less raw control |
| Best use case | Complex platforms, many services, custom operators | Small-to-medium apps that benefit from simple global deployment |

## When To Use Each

Use Kubernetes when:

- you need multiple tightly integrated services and operators
- you need full control over scheduling, networking, or platform policy
- you already run cluster-level observability, GitOps, and security tooling

Use Fly.io when:

- you want to ship one web app quickly with minimal platform management
- you want regional placement without building your own global platform stack
- you can accept platform conventions in exchange for speed and simplicity

My recommendation:

- for this course app, Fly.io is the faster path to a public multi-region deployment
- for the full course platform with ArgoCD, Rollouts, StatefulSets, Vault, and Prometheus, Kubernetes remains the more representative long-term environment
