# Lab 17 — Fly.io Edge Deployment

## Status

Local implementation for Lab 17 is complete:

- `app_python` prepared for Fly.io deployment with secrets, persistence, health checks, and a persisted `/visits` counter
- `app_go` prepared as the bonus deployment target
- `fly.toml` files created for both applications
- non-interactive deploy scripts created in [`scripts/lab17`](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/scripts/lab17)

Cloud deployment is currently blocked by missing Fly authentication on this machine:

```bash
fly auth whoami
# Error: no access token available. Please login with 'flyctl auth login'
```

Because of that, app URLs, dashboard screenshots, and live metrics cannot be honestly claimed yet.

## Deployment Summary

| Item | Python app | Go bonus app |
|------|------------|--------------|
| App name | `pavorkmert-devops-info-python` | `pavorkmert-devops-info-go` |
| Config file | [`app_python/fly.toml`](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/app_python/fly.toml) | [`app_go/fly.toml`](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/app_go/fly.toml) |
| Deploy script | [`deploy_python_fly.sh`](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/scripts/lab17/deploy_python_fly.sh) | [`deploy_go_bonus_fly.sh`](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/scripts/lab17/deploy_go_bonus_fly.sh) |
| Primary region | `ams` | `ams` |
| Extra regions | `iad`, `sin` | `iad`, `sin` |
| Internal port | `5000` | `8080` |
| Health endpoint | `/health` | `/health` |
| Persistence | Fly volume mounted to `/data` | Not required |
| Secrets | `API_KEY`, `DATABASE_URL` | Not required |
| Expected URL after deploy | `https://pavorkmert-devops-info-python.fly.dev` | `https://pavorkmert-devops-info-go.fly.dev` |

## Configuration Used

### Python app

- Docker source: [`app_python/Dockerfile`](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/app_python/Dockerfile)
- Fly config: internal port `5000`, HTTPS enabled, auto start/stop enabled
- Mounted volume: `app_data` -> `/data`
- Runtime env:
  - `HOST=0.0.0.0`
  - `PORT=5000`
  - `DATA_DIR=/data`

### Go bonus app

- Docker source: [`app_go/Dockerfile`](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/app_go/Dockerfile)
- Fly config: internal port `8080`, HTTPS enabled, auto start/stop enabled
- Multi-arch build corrected for Fly deployment by removing hardcoded `arm64`

## How Deployment Will Run

### Python app

```bash
cd /Users/pavorkmert/studying/DevOps/DevOps-Core-Course
fly auth login
export API_KEY_VALUE='replace-me'
export DATABASE_URL_VALUE='replace-me'
./scripts/lab17/deploy_python_fly.sh
```

What script does:

1. validates `app_python/fly.toml`
2. creates Fly app from config
3. creates regional volumes in `ams`, `iad`, `sin`
4. sets required secrets
5. deploys app
6. scales primary region to 2 machines
7. scales `iad` and `sin` to 1 machine each
8. prints status, checks, and machines

### Go bonus app

```bash
cd /Users/pavorkmert/studying/DevOps/DevOps-Core-Course
fly auth login
./scripts/lab17/deploy_go_bonus_fly.sh
```

## Application Changes for Lab 17

### Python app

[`app_python/app.py`](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/app_python/app.py) now includes:

- persisted visit counter with atomic file writes
- `/visits` endpoint for persistence verification
- Fly deployment metadata in `/`
- secret presence reporting as booleans only

This directly supports:

- secrets verification
- volume persistence verification
- multi-region environment introspection
- health check readiness

## Screenshots

Not yet collectible without successful Fly login and deployment.

After `fly auth login` and script execution, capture:

- Fly dashboard overview page
- Machines view showing `ams`, `iad`, `sin`
- Metrics page showing CPU, memory, and network
- `fly checks list` output
- `curl https://<app>.fly.dev/visits`

## Kubernetes vs Fly.io

| Aspect | Kubernetes | Fly.io |
|--------|------------|--------|
| Setup complexity | High: cluster, manifests, networking, storage, ingress | Low: app config plus `flyctl` |
| Deployment speed | Slower initial setup, flexible after that | Very fast for small apps |
| Global distribution | Powerful but more manual | Built-in regional placement |
| Cost for small apps | Often inefficient unless already operating cluster | Usually better fit for small edge services |
| Learning curve | Steep | Moderate |
| Control/flexibility | Maximum control | Lower, opinionated platform |
| Best use case | Complex platforms, custom infra, large teams | Small-to-medium apps, edge workloads, fast delivery |

## When to Use Each

Use Kubernetes when:

- you need full control over networking, operators, storage classes, and platform internals
- you run many services and already operate cluster tooling
- you need advanced scheduling and ecosystem integrations

Use Fly.io when:

- you want fast deployment without cluster management
- you need low-latency multi-region serving
- app is simple enough to fit PaaS constraints

Recommendation:

- for this course app, Fly.io is better for speed and simplicity
- for larger production platforms with many workloads, Kubernetes remains stronger

## Bonus Scope

Lab 17 file does not define a separate built-in bonus section.
To satisfy the user's request for "bonus task", the compiled Go service was prepared as an additional Fly deployment target with its own config and deploy script.
