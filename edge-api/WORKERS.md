# Cloudflare Workers Edge Deployment – Lab 17

## Deployment Summary

- **Worker URL**: `https://edge-api.acecution7.workers.dev`
- **Routes**:
  - `/` → General application information
  - `/health` → Health check endpoint
  - `/edge` → Edge metadata (colo, country, city, ASN, HTTP protocol, TLS version)
  - `/counter` → KV‑backed persistent counter
  - `/admin` → Protected admin endpoint (requires Bearer token)

- **Configuration**:
  - Plaintext var: `APP_NAME = "edge-api"`
  - Secrets: `API_TOKEN`, `ADMIN_EMAIL` (set via `wrangler secret put`)
  - KV namespace: `SETTINGS` (binding for persistent storage)

## Edge Metadata Example

Example response from `/edge` (based on actual request location):

```json
{
  "colo": "LAX",
  "country": "US",
  "city": "Los Angeles",
  "asn": "13335",
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3"
}
```

## Observability

Logs are emitted via `console.log()` in the worker. Example output from `npx wrangler tail`:

```
[2025-05-14T10:30:00.123Z] GET /health
[2025-05-14T10:30:05.456Z] GET /counter
[2025-05-14T10:31:12.789Z] GET /edge
```

Metrics (requests, errors, CPU time) can be viewed in the Cloudflare Dashboard under **Workers & Pages** → your worker → **Metrics**.

## Kubernetes vs Cloudflare Workers Comparison

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| Setup complexity | High (cluster provisioning, networking, storage classes) | Low (Wrangler CLI, built‑in dev server, no cluster) |
| Deployment speed | Minutes (build container, push to registry, rollout) | Seconds (`wrangler deploy`) |
| Global distribution | Manual (multi‑region clusters + global load balancer) | Automatic (300+ Points‑of‑Presence) |
| Cost (for small apps) | $5‑10+ per month (lowest VPS or cloud VM) | Free tier: 100k requests/day |
| State/persistence | PersistentVolumes, PVCs, StatefulSets | Workers KV, D1, R2 (separate products) |
| Control/flexibility | Full OS, any container, network policies, sidecars | Limited runtime, no arbitrary binaries, execution time limit |
| Best use case | Long‑running services, legacy workloads, complex microservices | Edge APIs, lightweight global functions, webhooks |

## When to Use Each

- **Kubernetes**:
  - Applications that need full control over the runtime environment.
  - Complex microservices with persistent storage and internal networking.
  - Workloads that run continuously and process large data.
- **Cloudflare Workers**:
  - Globally distributed APIs with low latency requirements.
  - Serverless event‑driven functions (webhooks, form handling, authentication proxies).
  - Simple state via KV (high‑read, moderate‑write).
- **Recommendation**: Use Workers for public‑facing REST APIs, A/B testing, or edge caching. Use Kubernetes for internal services, data processing, or when you need to run a complete container image (like your previous labs).

## Reflection

- **Easier than Kubernetes**: No cluster management; no manual replica counts, rolling updates, or service mesh. One command (`wrangler deploy`) publishes the code globally.
- **More constrained**: Cannot run arbitrary binaries; must use Workers‑compatible libraries. Execution duration limited to 30 seconds per request. No persistent local filesystem – state must go to KV or other bindings.
- **Not a Docker host**: I didn’t need to build or push a container. The Worker is written in TypeScript, directly deployed as a script. This radically simplifies the developer loop and eliminates container image management.

## Deployment and Operations

- **Initial deployment**: `npx wrangler deploy`
- **Rollback**: `npx wrangler rollback` or via dashboard **Versions & Deployments**
- **View logs**: `npx wrangler tail`
- **Environment variables**: Plaintext in `wrangler.jsonc`; secrets managed separately.
- **Persistence**: KV namespace bound to `SETTINGS` – the `/counter` endpoint stores and retrieves a visit count that survives redeploys.