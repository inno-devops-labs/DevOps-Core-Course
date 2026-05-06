# Lab 17 — Cloudflare Workers Deployment

## Deployment Summary

Project: `edge-api`

Planned public URL format:
- `https://edge-api.<your-subdomain>.workers.dev`

Main routes:
- `/` - app metadata and available routes
- `/health` - health check
- `/edge` - Cloudflare request metadata
- `/counter` - KV-backed persistent counter
- `/config` - config summary derived from vars and secrets

Configuration used:
- `APP_NAME` and `COURSE_NAME` as plaintext vars
- `API_TOKEN` and `ADMIN_EMAIL` as secrets
- `SETTINGS` as Workers KV namespace

---

## Evidence

After you run the deployment, add these artifacts here:
- Cloudflare dashboard screenshot
- `/edge` JSON response screenshot
- logs screenshot from `npx wrangler tail`
- deployment history screenshot
- KV counter output before and after redeploy

---

## Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| Setup complexity | High | Low |
| Deployment speed | Slower | Very fast |
| Global distribution | Manual or platform-managed | Automatic at the edge |
| Cost (for small apps) | Higher | Usually lower |
| State/persistence model | Pods, volumes, databases | KV, Durable Objects, bindings |
| Control/flexibility | Very high | More constrained |
| Best use case | Long-running services and complex systems | Lightweight global APIs and edge logic |

## When to Use Each

- Use Kubernetes when you need containers, custom runtimes, sidecars, persistent services, or heavy orchestration.
- Use Workers when you need a small HTTP API, fast global response, simple routing, and minimal infrastructure overhead.
- Recommendation: use Workers for edge-friendly request logic and Kubernetes for full application platforms.

## Reflection

- Workers feels easier for routing, deployment, and global access.
- Workers feels more constrained because it is not a Docker host and has a narrower runtime model.
- The biggest change is that you configure bindings and edge services instead of shipping an image to nodes.
