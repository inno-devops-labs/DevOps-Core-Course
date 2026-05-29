# Plumbing — `echo` service

A tiny Go HTTP service shipped by the course as **instructor-maintained plumbing**.
**You don't modify this code.** You deploy it alongside your own service starting in **Lab 9**.

## Why it exists

Through Lab 8 you ran a single Python service. When you reach Kubernetes (Lab 9),
running a **second** pod alongside it is the smallest topology in which `Service`,
kube-DNS, and cross-pod networking actually mean something. `echo` is that second pod.

## Endpoints

| Path | Behaviour |
|------|-----------|
| `GET /ping` | Returns `pong\n` — minimal smoke test |
| `* /echo` | Returns JSON containing the request body, headers, hostname, version, uptime, and a monotonic request counter — useful for verifying load balancing across replicas |
| `GET /healthz` | Returns `ok` (200) — wire this into `readinessProbe` and `livenessProbe` |
| `GET /metrics` | Prometheus text format — `echo_requests_total` counter + `echo_uptime_seconds` gauge |

## Local build

```bash
cd plumbing/echo
docker build -t echo:dev .
docker run --rm -p 8081:8081 echo:dev
curl -s localhost:8081/ping
curl -s localhost:8081/echo -d 'hello'
```

## Used in

- **Lab 9** — deployed as the 2nd service in your `default` namespace
- **Lab 10** — packaged as a subchart of your Helm chart (bonus track)
- **Labs 13–14** — second target of ArgoCD ApplicationSet + Argo Rollouts canary

The pre-built image is published from the course repo CI to `ghcr.io/inno-devops-labs/echo:vX.Y.Z`.

## Configuration

| Env var | Default | Purpose |
|---------|---------|---------|
| `PORT` | `8081` | Listen port |
| `VERSION` | `v1.0.0` | Reported in `/echo` JSON; useful for canary verification |
