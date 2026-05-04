# Lab 17 - Fly.io Edge Deployment

This document describes the Fly.io deployment for the DevOps Info Service.

## Environment

| Item | Value |
| --- | --- |
| App directory | `app_python` |
| Fly app name | `devops-info-vlad1mirzhidkov` |
| Primary region | `ams` |
| Extra regions | `iad`, `sin` |
| Runtime port | `8080` |
| Health endpoint | `/health` |
| Metrics endpoint | `/metrics` |
| Persistent data path | `/data/visits` |

The app already supports Fly.io because it reads `PORT`, binds to `0.0.0.0`,
exposes `/health` and `/metrics`, and stores visits in `VISITS_FILE`.

## Task 1 - Fly.io Setup

Install `flyctl` on Windows:

```powershell
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

Open a new terminal, then authenticate:

```powershell
fly auth login
fly auth whoami
fly version
```

Expected result:

```text
fly auth whoami
<your Fly.io account email or username>

fly version
flyctl v...
```

In this local workspace, `flyctl` was not installed at the time of preparing
the solution, so the deployment commands below are the commands to run after
authentication.

## Task 2 - Deploy Application

The Fly.io configuration is stored in `app_python/fly.toml`.

Important settings:

```toml
app = "devops-info-vlad1mirzhidkov"
primary_region = "ams"

[env]
  HOST = "0.0.0.0"
  PORT = "8080"
  VISITS_FILE = "/data/visits"

[http_service]
  internal_port = 8080
  force_https = true

  [[http_service.checks]]
    path = "/health"
```

Create the app without deploying yet:

```powershell
cd app_python
fly apps create devops-info-vlad1mirzhidkov --org personal
```

If the app name is already taken, choose another globally unique name and update
the `app` field in `fly.toml`.

Create a volume for the primary region:

```powershell
fly volumes create devops_info_data --region ams --size 1 --count 1
```

Deploy:

```powershell
fly deploy
```

Verify:

```powershell
fly status
fly checks list
fly logs
fly open
```

HTTP checks:

```powershell
$appUrl = "https://devops-info-vlad1mirzhidkov.fly.dev"

curl.exe -s "$appUrl/"
curl.exe -s "$appUrl/health"
curl.exe -s "$appUrl/visits"
curl.exe -s "$appUrl/metrics"
```

Expected health response:

```json
{"status":"healthy"}
```

The response also includes timestamp and uptime fields.

## Task 3 - Multi-Region Deployment

Add two more regions:

```powershell
fly regions add iad sin
fly regions list
```

Because this app mounts `/data`, each region that runs a Machine needs an
available Fly Volume with the same source name:

```powershell
fly volumes create devops_info_data --region iad --size 1 --count 1
fly volumes create devops_info_data --region sin --size 1 --count 1
```

Deploy again so Fly can place Machines in the configured regions:

```powershell
fly deploy
fly machines list
fly status
```

Scale to two Machines in the primary region:

```powershell
fly scale count 2 --region ams
```

If Fly reports that another volume is required in `ams`, create it and retry:

```powershell
fly volumes create devops_info_data --region ams --size 1 --count 1
fly scale count 2 --region ams
```

Latency test:

```powershell
Measure-Command { curl.exe -s "https://devops-info-vlad1mirzhidkov.fly.dev/health" | Out-Null }
fly ping
```

Record the observed latency:

| Test source | Endpoint | Result |
| --- | --- | --- |
| Local machine | `/health` | Fill with `Measure-Command` result |
| Fly edge | `fly ping` | Fill with nearest region output |

Fly routes requests through Anycast to the nearest edge and then to a healthy
Machine for the app.

## Task 4 - Secrets & Persistence

Set two secrets:

```powershell
fly secrets set LAB17_API_KEY="lab17-secret-value" LAB17_ENVIRONMENT="edge"
fly secrets list
```

Expected `fly secrets list` output contains only secret names and metadata, not
secret values:

```text
NAME                DIGEST                  CREATED AT
LAB17_API_KEY       ...                     ...
LAB17_ENVIRONMENT   ...                     ...
```

Verify secrets inside the Machine without exposing values publicly:

```powershell
fly ssh console -C "printenv | grep LAB17_"
```

Persistence test:

```powershell
$appUrl = "https://devops-info-vlad1mirzhidkov.fly.dev"
curl.exe -s "$appUrl/"
curl.exe -s "$appUrl/"
curl.exe -s "$appUrl/visits"

fly ssh console -C "cat /data/visits"
fly deploy
curl.exe -s "$appUrl/visits"
fly ssh console -C "cat /data/visits"
```

Expected result: the value in `/data/visits` remains after deployment because
`/data` is backed by a Fly Volume.

## Task 5 - Monitoring & Operations

Fly dashboard:

```text
https://fly.io/dashboard/devops-info-vlad1mirzhidkov
```

Useful operational commands:

```powershell
fly status
fly machines list
fly checks list
fly logs
fly releases
fly dashboard
```

Deploy a new version:

```powershell
fly deploy --strategy rolling
fly releases
```

Rollback if a release is bad:

```powershell
fly releases
fly deploy --image <previous-image-ref>
```

Health checks are configured in `fly.toml`:

```toml
[[http_service.checks]]
  grace_period = "20s"
  interval = "30s"
  method = "GET"
  timeout = "5s"
  path = "/health"
```

Custom metrics are exported to Fly's metrics integration:

```toml
[metrics]
  port = 8080
  path = "/metrics"
```

The application exposes Prometheus metrics such as:

```text
http_requests_total
http_request_duration_seconds
devops_info_endpoint_calls_total
```

## Screenshots

Place screenshots in `screenshots/lab17/`:

| Screenshot | What to capture |
| --- | --- |
| `01-dashboard.png` | Fly.io app dashboard |
| `02-machines-regions.png` | Machines running in `ams`, `iad`, `sin` |
| `03-metrics.png` | CPU, memory, network metrics |
| `04-health-checks.png` | Passing health checks |
| `05-volumes.png` | `devops_info_data` volume |

## Kubernetes vs Fly.io

| Aspect | Kubernetes | Fly.io |
| --- | --- | --- |
| Setup complexity | High: cluster, ingress, storage, monitoring, RBAC | Low: app config and `fly deploy` |
| Deployment speed | Slower initial setup, fast after Helm/GitOps is ready | Very fast for small services |
| Global distribution | Requires multiple clusters or advanced networking | Built in with Fly regions and Anycast |
| Cost for small apps | Can be expensive because the cluster has fixed overhead | Better for one or a few small apps |
| Learning curve | Steep: many primitives and controllers | Moderate: Machines, regions, volumes |
| Control/flexibility | Very high | Lower than Kubernetes but enough for many web apps |
| Best use case | Complex platforms, many services, strict customization | Globally distributed web apps and APIs |

## When to Use Kubernetes

Use Kubernetes when:

- the system contains many services and teams;
- custom networking, operators, admission policies, or service mesh are needed;
- workloads must run in a specific cloud or private environment;
- GitOps, progressive delivery, and platform-level controls are important.

## When to Use Fly.io

Use Fly.io when:

- the application is a small or medium web service;
- global low-latency deployment matters;
- the team wants to avoid cluster management;
- Docker packaging is enough and platform defaults are acceptable.

## Recommendation

For this DevOps Info Service, Fly.io is the better operational choice because
the app is a single HTTP service with simple persistence and health checks.
Kubernetes is more powerful for the earlier labs because it demonstrates
production platform primitives, but Fly.io reaches a working global deployment
with less infrastructure code.

## Final Checklist

- [x] Fly configuration created
- [x] Docker-based deployment configured
- [x] HTTP health check configured
- [x] Metrics endpoint configured
- [x] Volume mount configured for `/data/visits`
- [x] Multi-region commands documented
- [x] Secrets commands documented
- [x] Kubernetes vs Fly.io comparison documented
- [ ] `flyctl` installed locally
- [ ] Fly.io login completed
- [ ] App deployed to Fly.io
- [ ] Screenshots captured from Fly.io dashboard
