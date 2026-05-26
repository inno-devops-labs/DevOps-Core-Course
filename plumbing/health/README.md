# Plumbing — `health` service

A second instructor-maintained plumbing service. Introduced in **Lab 13** as the
**third** service in your topology — the additional target ArgoCD's `ApplicationSet`
needs in order to generate multiple Applications (the pattern only makes sense at ≥ 3 apps).

## Endpoints

| Path | Behaviour |
|------|-----------|
| `GET /` | JSON status — service, version, hostname, Go version, uptime, request counter |
| `GET /healthz` | Returns `ok` (200) for probes |
| `GET /metrics` | Prometheus text format — `health_requests_total`, `health_uptime_seconds` |

## Used in

- **Lab 13** — third Application in your ArgoCD ApplicationSet (Python service + echo + health)
- **Lab 14** — extra rollout target for blue-green vs canary experimentation
- **Lab 16** — included in cluster-wide kube-prometheus scrape

The pre-built image is published from the course repo CI to `ghcr.io/inno-devops-labs/health:vX.Y.Z`.

## Configuration

| Env var | Default |
|---------|---------|
| `PORT` | `8082` |
| `VERSION` | `v1.0.0` |
