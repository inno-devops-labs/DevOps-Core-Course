# Lab 17 — Fly.io Edge Deployment

## 1. Fly.io Setup

### Installation

```bash
brew install flyctl
fly auth login    # opens browser
fly auth whoami   # verify login
fly version
```

![flyctl version and auth whoami](../k8s/img/lab17/flyctl-version.png)

### Platform Concepts

| Concept | Description |
|---------|-------------|
| **Fly Machine** | A lightweight VM (microVM) that runs your container. Each Machine is a separate compute unit with its own CPU/RAM. Machines can be started/stopped automatically based on traffic. |
| **Fly Volume** | Persistent block storage attached to a Machine. Survives restarts and redeployments. Like a Kubernetes PVC but managed by Fly. |
| **Region** | A geographic location where Machines run (e.g., `ams` = Amsterdam). Fly routes incoming requests to the nearest available Machine automatically. |
| **Edge deployment** | Machines run close to end users in 30+ worldwide regions, minimising latency without you managing infrastructure. |

**Free tier includes:** 3 shared-cpu-1x VMs (256 MB RAM), 3 GB persistent storage, 160 GB outbound bandwidth.

---

## 2. Application Deployment

### Prepare and Launch

```bash
cd app_python
fly launch
# App name: devops-info-service
# Region: ams (Amsterdam)
# Postgres: No
# Redis: No
# Deploy now: Yes
```

The `fly.toml` configuration file was generated and adjusted:
- `internal_port = 5001` — matches the app's `PORT` environment variable
- `path = "/health"` — uses the existing health check endpoint
- `auto_stop_machines = true` — cost-efficient: Machine sleeps when idle

### Deploy

```bash
fly deploy
```

![fly deploy output — build and release](../k8s/img/lab17/deploy-output.png)

### Verify

```bash
fly status
fly open        # open app URL in browser
fly logs        # view live logs
```

![fly status — machines running](../k8s/img/lab17/fly-status.png)

All endpoints verified:

| Endpoint | Response |
|----------|----------|
| `/` | `{"hostname": "...", "os": "Linux", ...}` |
| `/health` | `{"status": "healthy"}` |
| `/visits` | `{"visits": N}` |

![App running in browser — / and /health](../k8s/img/lab17/app-running.png)

---

## 3. Multi-Region Deployment

### Add Regions

```bash
fly regions add iad sin
fly regions list
```

![fly regions list — ams, iad, sin](../k8s/img/lab17/regions-list.png)

Regions selected:
- `ams` — Amsterdam (primary, closest to me)
- `iad` — Virginia, USA (covers North America)
- `sin` — Singapore (covers Asia-Pacific)

### Verify Distribution

```bash
fly machines list
```

![fly machines list — one machine per region](../k8s/img/lab17/machines-list.png)

### Scale in Primary Region

```bash
fly scale count 2 --region ams
fly machines list
```

![Two machines in ams region](../k8s/img/lab17/machines-scaled.png)

### Latency Test

```bash
fly ping
```

| Region | Avg RTT |
|--------|---------|
| ams    | ~8 ms   |
| iad    | ~95 ms  |
| sin    | ~155 ms |

Fly routes each request to the Machine with the lowest latency. A user in Singapore is automatically served by the `sin` Machine — no DNS tricks or load balancer configuration required.

---

## 4. Secrets & Persistence

### Configure Secrets

```bash
fly secrets set USERNAME="devops-user" API_KEY="secret-key-123"
fly secrets list
```

![fly secrets list — names only (values hidden)](../k8s/img/lab17/secrets-list.png)

Secrets are injected as environment variables at runtime. They are encrypted at rest and never visible in logs or `fly.toml`. The app reads them with `os.getenv("USERNAME")`.

### Attach Volume

```bash
fly volumes create devops_data --size 1 --region ams
```

Add to `fly.toml`:

```toml
[mounts]
  source = "devops_data"
  destination = "/data"
```

```bash
fly deploy
```

### Verify Persistence

```bash
fly ssh console
cat /data/visits    # read current visit count
exit

# Make several requests to increment visits
curl https://devops-info-service.fly.dev/visits

# Redeploy (simulates restart)
fly deploy

# Check persistence after redeploy:
fly ssh console
cat /data/visits    # same value as before — data survived!
```

![/data/visits value before and after redeploy](../k8s/img/lab17/persistence-test.png)

---

## 5. Monitoring & Operations

### Fly.io Dashboard Metrics

```bash
# View in browser:
# https://fly.io/dashboard → select app → Metrics tab
```

![Fly.io dashboard — CPU, memory, network](../k8s/img/lab17/dashboard-metrics.png)

Metrics visible in the dashboard:
- CPU usage per Machine
- Memory usage
- HTTP request rate and latency
- Machine state (started / stopped)

### Deployment History

```bash
fly releases
```

![fly releases — version history](../k8s/img/lab17/releases.png)

```bash
# Rolling deployment (zero-downtime):
fly deploy --strategy rolling

# Immediate replacement:
fly deploy --strategy immediate
```

Fly supports atomic rollbacks: if the new release fails health checks, the previous release is automatically restored.

### Health Checks

Configured in `fly.toml`:

```toml
[checks]
  [checks.health]
    type = "http"
    port = 5001
    path = "/health"
    interval = "10s"
    timeout = "2s"
    grace_period = "30s"
```

Fly polls `/health` every 10 seconds. If 3 consecutive checks fail, the Machine is restarted. The `grace_period` gives the app 30 seconds to start before checks begin.

---

## 6. Kubernetes vs Fly.io Comparison

| Aspect | Kubernetes (Labs 9–16) | Fly.io |
|--------|------------------------|--------|
| **Setup complexity** | High — cluster, namespaces, RBAC, networking | Minimal — `fly launch` in 2 minutes |
| **Deployment speed** | Minutes (image pull, pod scheduling) | ~30 seconds (optimised for fast deploys) |
| **Global distribution** | Manual — requires multi-cluster federation | Built-in — `fly regions add` |
| **Cost (small apps)** | Medium — cluster nodes run 24/7 | Low — Machines sleep when idle (free tier available) |
| **Learning curve** | Very steep | Gentle — abstracts infrastructure |
| **Control/flexibility** | Maximum — full cluster access, custom CRDs | Medium — limited to Fly primitives |
| **Best use case** | Complex microservices, stateful workloads | Simple services, APIs, global low-latency apps |

### When to Use Kubernetes

- Microservices architecture with many interdependent services
- Stateful workloads (databases, queues) needing fine-grained storage control
- Organisation already has Kubernetes expertise and tooling
- Need for custom operators, CRDs, or advanced scheduling
- Compliance requirements requiring full infrastructure control

### When to Use Fly.io

- Small to medium web apps and APIs that need global reach
- Early-stage projects where time-to-deploy matters more than customisation
- Apps with variable traffic that benefit from auto-stop/start
- Teams without Kubernetes expertise
- Prototypes and side projects where cluster cost is prohibitive

### Recommendation

For the DevOps Info Service specifically — **Fly.io is the better fit**. It is a stateless web API with simple health checks and no inter-service dependencies. Fly provides global distribution, HTTPS, health-check-based restarts, and zero-downtime deploys out of the box — all without managing a cluster. Kubernetes would be overkill unless this service were part of a larger ecosystem requiring shared networking, custom autoscaling policies, or advanced rollout strategies (which we do have with Argo Rollouts from Lab 14).
