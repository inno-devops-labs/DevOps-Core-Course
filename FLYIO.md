# Lab 17 - Fly.io Edge Deployment

## Deployment Summary

The Python DevOps Info Service was prepared for Fly.io deployment with a
Fly-specific configuration in `app_python/fly.toml`.

| Item | Value |
| --- | --- |
| Fly app name | `ellilin-devops-info-lab17` |
| Runtime app | `app_python` |
| Dockerfile | `app_python/Dockerfile` |
| Internal port | `8000` |
| Primary region | `ams` (Amsterdam) |
| Additional regions | `iad` (Virginia), `sin` (Singapore) |
| Persistent mount | `devops_info_data` mounted at `/data` |
| Public URL | Blocked until Fly account payment verification is completed |

## Final Status

All repository-side work for Lab 17 is complete:

- `flyctl` is installed and authenticated.
- `app_python/fly.toml` is present and validated by `fly config validate`.
- The Docker image builds successfully from `app_python/Dockerfile`.
- The application runs locally in Docker with the same runtime settings expected
  on Fly.io.
- `/health`, `/secrets`, and `/visits` were verified locally.
- The application has a safe `/secrets` endpoint for checking Fly secrets without
  exposing secret values.
- Unit tests and formatting/lint checks pass locally.

The only incomplete items are the real Fly.io deployment artifacts: public app
URL, multi-region machines, dashboard metrics, and screenshots. These are blocked
by Fly.io account payment verification, not by the application or repository
configuration.

## Current Account Blocker

`flyctl` was installed and authentication succeeded:

```bash
fly auth login
# successfully logged in as elechka.ku@gmail.com
```

Creating the Fly app is blocked by Fly.io account verification:

```bash
fly apps create ellilin-devops-info-lab17 --org personal
```

Result:

```text
Error: We need your payment information to continue! Add a credit card or buy credit:
https://fly.io/dashboard/elli/billing
```

The same blocker was reproduced after retrying app creation:

```text
Error: We need your payment information to continue! Add a credit card or buy credit:
https://fly.io/dashboard/elli/billing
```

The lab text says no credit card is required, but the current Fly.io account
policy requires verification before new apps can be deployed. The repository is
ready for deployment once billing verification is completed.

## Fly Configuration

`app_python/fly.toml` configures:

- Docker build from the existing application Dockerfile.
- HTTPS service routing to container port `8000`.
- HTTP health checks on `/health`.
- Auto-start and auto-stop machines for free-tier-friendly behavior.
- A persistent volume mounted at `/data` for the visits counter.
- 256 MB shared CPU machines.

## Deployment Commands

Run from `app_python` after the account is verified:

```bash
fly apps create ellilin-devops-info-lab17 --org personal
fly volumes create devops_info_data --size 1 --region ams
fly volumes create devops_info_data --size 1 --region ams
fly volumes create devops_info_data --size 1 --region iad
fly volumes create devops_info_data --size 1 --region sin
fly secrets set LAB17_API_KEY="lab17-api-key" LAB17_DEPLOYMENT_TOKEN="lab17-token"
fly deploy --strategy rolling
fly regions add iad sin
fly scale count 2 --region ams
fly scale count 1 --region iad
fly scale count 1 --region sin
```

Two `ams` volumes are intentional because the lab requires scaling the primary
region to two machines, and each Fly Machine needs its own attached volume.

## Verification Commands

```bash
fly status
fly machines list
fly regions list
fly secrets list
fly checks list
fly logs
fly releases
fly ping
curl -sS https://ellilin-devops-info-lab17.fly.dev/health
curl -sS https://ellilin-devops-info-lab17.fly.dev/secrets
curl -sS https://ellilin-devops-info-lab17.fly.dev/visits
```

Expected endpoint behavior:

- `/health` returns `{"status":"healthy", ...}`.
- `/secrets` reports `LAB17_API_KEY` and `LAB17_DEPLOYMENT_TOKEN` as configured
  without returning their secret values.
- `/visits` returns the persisted counter file path `/data/visits`.
- `/metrics` exposes Prometheus metrics.

## Local Readiness Verification

The application image was built successfully:

```bash
docker build -t devops-info-service:lab17 .
```

The container was run with the same secret environment variables expected on
Fly.io:

```bash
docker run --rm -d --name devops-lab17-test -p 8087:8000 \
  -e LAB17_API_KEY=local-key \
  -e LAB17_DEPLOYMENT_TOKEN=local-token \
  devops-info-service:lab17
```

Local endpoint checks passed:

Code quality and test checks also passed:

```bash
./venv/bin/ruff check app.py tests/test_app.py
./venv/bin/ruff format --check app.py tests/test_app.py
./venv/bin/python -m pytest tests -q --no-cov
```

Result:

```text
All checks passed.
2 files already formatted.
26 passed.
```

```bash
curl -sS http://127.0.0.1:8087/health
```

```json
{"status":"healthy","timestamp":"2026-05-13T20:17:37.619622+00:00","uptime_seconds":31}
```

```bash
curl -sS http://127.0.0.1:8087/secrets
```

```json
{"secrets":{"LAB17_API_KEY":{"configured":true,"value":"set"},"LAB17_DEPLOYMENT_TOKEN":{"configured":true,"value":"set"}}}
```

```bash
curl -sS http://127.0.0.1:8087/visits
```

```json
{"file":"/data/visits","visits":0}
```

## Secrets

The service expects two Fly secrets:

| Secret | Purpose |
| --- | --- |
| `LAB17_API_KEY` | Example application API key for lab verification |
| `LAB17_DEPLOYMENT_TOKEN` | Example deployment/runtime token for lab verification |

The `/secrets` endpoint only reports whether each secret is present. It never
returns raw secret values.

## Persistence

The Python service already persists the root endpoint visit counter to
`VISITS_FILE`. On Fly.io this is configured as:

```toml
VISITS_FILE = "/data/visits"
```

The Fly volume mount is:

```toml
[[mounts]]
  source = "devops_info_data"
  destination = "/data"
```

Persistence can be verified by calling `/`, redeploying, and checking that
`/visits` retains the previous counter value.

## Monitoring and Operations

Fly.io operations to use after deployment:

| Task | Command or location |
| --- | --- |
| Dashboard | `https://fly.io/dashboard/elli/apps/ellilin-devops-info-lab17` |
| Machine state | `fly machines list` |
| Logs | `fly logs` |
| Health checks | `fly checks list` |
| Release history | `fly releases` |
| Rolling deploy | `fly deploy --strategy rolling` |
| Immediate deploy | `fly deploy --strategy immediate` |
| Metrics | Dashboard Metrics tab |

## Kubernetes vs Fly.io

| Aspect | Kubernetes | Fly.io |
| --- | --- | --- |
| Setup complexity | Requires cluster, ingress, registry, RBAC, manifests, and operational tooling | Requires account, `flyctl`, Dockerfile, and `fly.toml` |
| Deployment speed | Slower initial setup, fast once CI/CD and GitOps are ready | Very fast for Dockerized apps after account verification |
| Global distribution | Requires multi-region clusters or a managed global platform | Built in through Fly regions and edge routing |
| Cost for small apps | Usually higher because the cluster control plane and nodes run continuously | Low for small apps with auto-start and auto-stop machines |
| Learning curve | Steep; many primitives and failure modes | Moderate; fewer concepts and simpler workflow |
| Control/flexibility | Maximum control over scheduling, networking, operators, policies, and storage | Less control, but enough for many web services and APIs |
| Best use case | Complex platforms, many services, strict customization, internal infrastructure | Small to medium global apps, APIs, prototypes, edge workloads |

## When to Use Each

Use Kubernetes when the system needs advanced orchestration, many cooperating
services, custom controllers, strict network policy, specialized workloads, or
deep platform control.

Use Fly.io when the goal is to deploy a Dockerized web application globally with
minimal infrastructure management, simple scaling, built-in TLS, edge routing,
and straightforward operations.

For this DevOps Info Service, Fly.io is the pragmatic deployment target because
the app is a small stateless API with one optional persistent counter file. A
Kubernetes deployment remains valuable for learning and for larger systems, but
it is operationally heavier than this service needs.

## Checklist

- [x] `flyctl` installed.
- [x] Fly.io authentication completed.
- [x] Docker image builds locally.
- [x] Health endpoint verified locally.
- [x] Secret presence endpoint implemented and verified locally.
- [x] Persistent visits file path verified locally.
- [x] `fly.toml` created.
- [x] Kubernetes vs Fly.io comparison documented.
- [ ] Fly app created, blocked by Fly.io payment verification.
- [ ] Multi-region machines deployed, blocked by Fly.io payment verification.
- [ ] Dashboard, machines, and metrics screenshots captured, blocked by Fly.io
      payment verification.
