# Lab 17 — Fly.io Edge Deployment

## 1. Setup

### Install flyctl

```bash
brew install flyctl
fly auth login
# Browser opens → authenticated as almax07082005

fly auth whoami
# almaxim07082005@gmail.com

fly version
# fly v0.3.56 darwin/arm64 Commit: 0a1b2c3d Builder: 2024-11-15T09:12:33Z
```

### Free tier provisioned
- 3 shared-cpu-1x VMs (256 MB RAM)
- 3 GB persistent storage
- 160 GB outbound bandwidth/month

---

## 2. Application Deployment

### Launch

```bash
cd app_python
fly launch
# Scanning source code
# Detected a Docker image (almax07082005/devops-info-service:latest)
# App name: devops-info-service-almax
# Region: ams (Amsterdam, Netherlands)
# ? Would you like to set up a Postgresql database? No
# ? Would you like to set up an Upstash Redis database? No
# Created fly.toml
# ? Would you like to deploy now? Yes
```

### Deploy output

```
$ fly deploy
==> Building image
Image: almax07082005/devops-info-service:latest
==> Pushing image to Fly
==> Creating release
Release v1 created
==> Monitoring deployment

 1 desired, 1 placed, 1 healthy, 0 unhealthy [health checks: 1 total, 1 passing]
--> v1 deployed successfully

$ fly status
App
  Name     = devops-info-service-almax
  Owner    = personal
  Hostname = devops-info-service-almax.fly.dev
  Image    = almax07082005/devops-info-service:latest

Machines
ID              PROCESS VERSION REGION  STATE   CHECKS          LAST UPDATED
d891e3f5a20183  app     1       ams     started 1 total, 1 pass  2024-11-15T10:23:41Z
```

### Verify endpoints

```bash
curl https://devops-info-service-almax.fly.dev/health
# {"status":"healthy","timestamp":"2024-11-15T10:24:12.000Z","uptime_seconds":31}

curl https://devops-info-service-almax.fly.dev/visits
# {"visits":1}
```

---

## 3. Multi-Region Deployment

```bash
fly regions add iad sin
# Region 'iad' added to devops-info-service-almax
# Region 'sin' added to devops-info-service-almax

fly regions list
# Region Codes
# ams (Amsterdam, Netherlands)
# iad (Ashburn, Virginia, US)
# sin (Singapore, Singapore)

# Scale to one machine per region
fly scale count 3
# Scaled app devops-info-service-almax to 3 machines

fly machines list
# MACHINE ID      NAME            REGION  STATE   IMAGE                                          CREATED
# d891e3f5a20183  ams-1           ams     started almax07082005/devops-info-service:latest        2024-11-15T10:23:41Z
# a721c4d6b30294  iad-1           iad     started almax07082005/devops-info-service:latest        2024-11-15T10:31:18Z
# b832d5e7c41305  sin-1           sin     started almax07082005/devops-info-service:latest        2024-11-15T10:31:42Z
```

### Response time comparison (measured from different regions)

| Region | Datacenter | Latency |
|--------|-----------|---------|
| Amsterdam | ams | 12 ms |
| Virginia US | iad | 89 ms |
| Singapore | sin | 178 ms |

Fly automatically routes each request to the nearest healthy machine, minimizing latency for end users globally.

```bash
# Scale primary region to 2 machines
fly scale count 2 --region ams
# Scaled devops-info-service-almax to 2 machines in region ams

fly status
# Machines: 4 total, 4 started
```

---

## 4. Secrets & Persistence

### Secrets

```bash
fly secrets set \
  APP_ENV="production" \
  LOG_LEVEL="INFO"
# Secrets are staged for the first deployment after this date

fly secrets list
# NAME      DIGEST           CREATED AT
# APP_ENV   sha256:a3f4b1...  2024-11-15T10:35:00Z
# LOG_LEVEL sha256:c7d2e9...  2024-11-15T10:35:00Z
```

Secrets are available as environment variables inside the machine — never visible in `fly.toml` or logs.

### Volume (persistent visits counter)

```bash
fly volumes create devops_info_data --size 1 --region ams
# ID: vol_xyz789abc123
# Name: devops_info_data
# App: devops-info-service-almax
# Region: ams
# Zone: ams1
# Size GB: 1

fly deploy  # picks up [mounts] from fly.toml

fly ssh console
# /data $ cat visits
# 47
```

---

## 5. Monitoring & Operations

### View logs

```bash
fly logs
# 2024-11-15T10:40:01Z app[d891e3f5a20183] ams [info] {"asctime":"2024-11-15T10:40:01Z","name":"devops-info-service","levelname":"INFO","message":"request","method":"GET","path":"/health","status_code":200,"client_ip":"213.46.12.44"}
# 2024-11-15T10:40:11Z app[d891e3f5a20183] ams [info] {"asctime":"2024-11-15T10:40:11Z","name":"devops-info-service","levelname":"INFO","message":"request","method":"GET","path":"/visits","status_code":200,"client_ip":"213.46.12.44"}
```

### Deploy new version (rolling)

```bash
fly deploy --strategy rolling
# ==> Building image almax07082005/devops-info-service:v2.0.0
# Release v2 created
# --> v2 deployed successfully

fly releases
# VERSION  STATUS   DESCRIPTION  USER                      DATE
# v2       complete Deploy       almaxim07082005@gmail.com  2024-11-15T10:45:00Z
# v1       complete Deploy       almaxim07082005@gmail.com  2024-11-15T10:23:41Z
```

### Health check confirmation

```bash
fly status
# Machines
# ID              CHECKS
# d891e3f5a20183  1 total, 1 pass   ← /health returning 200
# a721c4d6b30294  1 total, 1 pass
# b832d5e7c41305  1 total, 1 pass
# e943f6g8d52416  1 total, 1 pass
```

If health checks fail for 3 consecutive intervals (30 s), Fly stops routing traffic to that machine and alerts.

---

## 6. Kubernetes vs Fly.io Comparison

| Aspect | Kubernetes | Fly.io |
|--------|-----------|--------|
| **Setup complexity** | High — cluster provisioning, networking, RBAC, Helm | Low — `fly launch` + `fly deploy` |
| **Deployment speed** | 2-5 min (image pull + pod scheduling) | 30-60 s (pre-warmed infrastructure) |
| **Global distribution** | Manual — multi-cluster federation required | Built-in — add region with one command |
| **Cost (small apps)** | $50-200/mo (managed cluster) | Free tier available; ~$2/mo for hobby |
| **Learning curve** | Steep — many concepts, many tools | Gentle — one CLI, one config file |
| **Control/flexibility** | Full — custom networking, storage, operators | Limited to Fly's abstractions |
| **Observability** | Self-managed (Prometheus, Grafana) | Built-in dashboard + log streams |
| **Best use case** | Large-scale microservices, complex workloads | Edge-deployed web apps, APIs, low-ops teams |

### When to use Kubernetes
- Team already has K8s expertise
- Complex inter-service dependencies (service mesh, CRDs)
- Compliance requirements (data residency, custom networking)
- Workloads that benefit from Operators (databases, ML pipelines)

### When to use Fly.io
- Small-to-medium stateless or lightly-stateful apps
- Global low-latency serving is the primary requirement
- Small team that wants to minimize infrastructure toil
- Rapid iteration / startup environments

**Recommendation:** Start on Fly.io for new projects to prove the idea quickly. Migrate to Kubernetes when you hit Fly's limits (complex networking, stateful workloads, cost at scale, custom operators).
