# Cloudflare Workers Lab 17

## Deployment Summary
- Worker URL: https://edge-api.vundirov-lab17.workers.dev/
- Main routes: `/`, `/health`, `/edge`, `/counter`
- Configuration:
  - Vars: `APP_NAME`, `COURSE_NAME`
  - KV binding: `SETTINGS`

## Evidence
![](/edge-api/docs/screenshots/test_curl.png)

![](/edge-api/docs/screenshots/test_curl_cloudflare.png)

![](/edge-api/docs/screenshots/test_curl_cloudflare_ui.png)

![](/edge-api/docs/screenshots/test_curl_location.png)

![](/edge-api/docs/screenshots/terminal_logs.png)


![](/edge-api/docs/screenshots/ui_metrics.png)

## Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
| --- | --- | --- |
| Setup complexity | High: cluster setup, ingress, storage, manifests | Low: single config + CLI deploy |
| Deployment speed | Slower: build/push image, rollout | Fast: deploy script, instant edge |
| Global distribution | Manual: multi-region clusters + LB | Automatic: runs at Cloudflare edge |
| Cost (for small apps) | Higher baseline (nodes, control plane) | Low, usage-based |
| State/persistence model | Stateful via PVs, databases, operators | External services (KV/D1/DO), eventual consistency |
| Control/flexibility | Full runtime control, any container | Constrained runtime and limits |
| Best use case | Complex services, long-running workloads | Lightweight APIs, edge logic |

## When to Use Each
- Kubernetes: complex microservices, long-running jobs, custom runtimes, heavy stateful apps
- Workers: small APIs, request routing, caching, edge auth, quick global exposure
- Recommendation: use Workers for this lab and small global APIs; use Kubernetes when you need full control and long-running services

## Reflection
- Easier than Kubernetes: deploy and global routing with almost no infra setup
- More constrained: runtime limits, no container images, fewer system-level controls
- What changed without Docker: no build/push image step, use bindings and serverless APIs instead of containerized services
