# Lab 17 — Fly.io Edge Deployment Report

Date: 2026-05-10  
Application: `devops-info-service`  
Source directory: `app_python/`  
Fly.io app name prepared: `devops-info-egrapa-lab17`

## Status Summary

The application is prepared for Fly.io deployment and the local Docker image was built and verified successfully. `flyctl` is installed and authentication was verified, but the Fly.io account is not fully enabled for creating/running Fly Machines because billing/account activation is incomplete. Because of this external platform limitation, I did not create paid cloud resources.

Evidence files:

- `docs/lab17-evidence/fly-cli.txt`
- `docs/lab17-evidence/docker-local.txt`
- `docs/lab17-evidence/deployment-blocker.txt`

## Fly.io Setup

`flyctl` is installed at:

```text
/home/egrapa/.fly/bin/fly
```

Version verified:

```text
flyctl v0.4.49 linux/amd64
BuildDate: 2026-05-07T08:59:44Z
```

Authentication was verified with `fly auth whoami`. The report evidence redacts the email address for privacy.

Available Fly regions were checked with `fly platform regions`. Planned multi-region deployment:

| Region | Code | Purpose |
|--------|------|---------|
| Amsterdam | `ams` | Primary region |
| Ashburn, Virginia | `iad` | North America edge region |
| Singapore | `sin` | Asia Pacific edge region |

## Application Preparation

The application already supports Fly.io-style runtime configuration:

- Flask app binds to `HOST`, default `0.0.0.0`
- Port is configurable via `PORT`
- Health endpoint exists at `/health`
- Metrics endpoint exists at `/metrics`
- Persistent visits counter exists at `/visits`
- Visit counter storage is configurable via `VISITS_FILE`

Fly.io configuration was added in `app_python/fly.toml`.

Important configuration:

```toml
app = "devops-info-egrapa-lab17"
primary_region = "ams"

[env]
  HOST = "0.0.0.0"
  PORT = "5000"
  VISITS_FILE = "/data/visits"

[mounts]
  source = "data"
  destination = "/data"

[http_service]
  internal_port = 5000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[checks.health]
  type = "http"
  port = 5000
  path = "/health"
```

## Local Verification

Docker image build:

```bash
cd app_python
docker build -t devops-info-service:lab17-local .
```

Result:

```text
Successfully built 4c7f4317d560
Successfully tagged devops-info-service:lab17-local
```

Container run:

```bash
docker run -d --rm \
  --name devops-info-service-lab17-local \
  -p 5000:5000 \
  -e APP_ENV=lab17-local \
  -e APP_DISPLAY_NAME=devops-info-service \
  devops-info-service:lab17-local
```

Endpoint checks:

| Endpoint | Result | Local response time |
|----------|--------|---------------------|
| `/` | HTTP 200 | 0.014326s |
| `/health` | HTTP 200 | 0.001111s |
| `/visits` | HTTP 200 | 0.001627s |
| `/metrics` | Prometheus metrics returned | verified |

Health response:

```json
{"status":"healthy","timestamp":"2026-05-10T17:31:25.571953+00:00","uptime_seconds":7}
```

## Planned Fly.io Deployment Commands

These commands are ready to run once the Fly.io account is fully enabled:

```bash
cd app_python

fly apps create devops-info-egrapa-lab17
fly volumes create data --size 1 --region ams --app devops-info-egrapa-lab17

fly secrets set \
  APP_ENV="production" \
  APP_DISPLAY_NAME="devops-info-service-fly" \
  --app devops-info-egrapa-lab17

fly deploy --app devops-info-egrapa-lab17

fly regions add iad sin --app devops-info-egrapa-lab17
fly scale count 2 --region ams --app devops-info-egrapa-lab17

fly status --app devops-info-egrapa-lab17
fly machines list --app devops-info-egrapa-lab17
fly checks list --app devops-info-egrapa-lab17
fly releases --app devops-info-egrapa-lab17
fly logs --app devops-info-egrapa-lab17
```

Expected public URL after deployment:

```text
https://devops-info-egrapa-lab17.fly.dev
```

## Deployment Blocker

The cloud deployment was not completed because the current Fly.io account is logged in but not fully enabled for running Fly Machines. Completing the deployment requires activating the account/billing on Fly.io. This is outside the repository and local environment.

No Fly Machines, volumes, or billable resources were created during this report.

## Screenshots / Dashboard Evidence

Dashboard screenshots could not be captured because the application was not deployed to Fly.io. Once the account is enabled and the planned commands are run, the following screenshots should be added:

- Fly.io app overview
- Machines list showing `ams`, `iad`, and `sin`
- Metrics dashboard showing CPU, memory, and network
- Health check status
- Releases/deployment history

## Kubernetes vs Fly.io Comparison

| Aspect | Kubernetes | Fly.io |
|--------|------------|--------|
| Setup complexity | High: cluster, nodes, ingress, controllers, monitoring | Low: app config plus `fly deploy` |
| Deployment speed | Slower initial setup, fast after pipelines exist | Very fast for small containerized apps |
| Global distribution | Requires multiple clusters or advanced networking | Built in with Fly regions and edge routing |
| Cost for small apps | Often higher because cluster overhead exists | Usually cheaper and simpler for small services |
| Learning curve | Steep: pods, services, ingress, Helm, RBAC, operators | Moderate: apps, machines, regions, volumes |
| Control/flexibility | Maximum control over infrastructure and platform behavior | Less control, but much less operational burden |
| Best use case | Complex platforms, many services, strict customization | Small to medium apps needing simple global deployment |

## When To Use Each

Use Kubernetes when the project needs full platform control, many cooperating services, custom networking, internal platform tooling, strict workload isolation, or advanced scheduling.

Use Fly.io when the project is a containerized application that should be deployed quickly, run near users globally, and avoid cluster management overhead.

For this Flask service, Fly.io is the better operational fit: the app is small, stateless except for a simple visit counter, exposes a health endpoint, and can be deployed globally with much less infrastructure than Kubernetes.

## Checklist

- [x] Fly.io CLI installed
- [x] Fly.io authentication verified
- [x] Application Docker image builds locally
- [x] Application endpoints verified locally
- [x] Fly.io `fly.toml` created
- [x] Health check configured
- [x] Persistent volume mount configured
- [x] Multi-region deployment plan documented
- [x] Secrets commands documented
- [x] Kubernetes vs Fly.io comparison documented
- [ ] Cloud deployment completed: blocked by incomplete Fly.io account/billing activation
- [ ] Dashboard screenshots captured: blocked until deployment is possible
