# Lab 17 — Cloudflare Workers Edge Deployment

## 1. Deployment Summary

**Worker URL:** `https://edge-api.merkulovlr.workers.dev`

**Account:** merkulovlr@gmail.com  
**Worker name:** edge-api  
**CLI version:** wrangler 4.87.0

### Routes

| Path | Description | Auth |
|------|-------------|------|
| `GET /` | Service metadata, app info | Public |
| `GET /health` | Health check | Public |
| `GET /edge` | Cloudflare edge metadata (`colo`, `country`, `city`, `asn`, `tlsVersion`) | Public |
| `GET /counter` | KV-backed persistent visit counter | Public |

### Configuration

**Plaintext vars** (`wrangler.jsonc`):
```json
"vars": {
  "APP_NAME": "edge-api",
  "COURSE_NAME": "devops-core"
}
```
Plaintext vars are not suitable for secrets because they appear in plain text in the config file, in deployment history, and are readable by anyone with access to the Wrangler project. Secrets are encrypted at rest and never revealed after upload.

**Secrets** (set via `npx wrangler secret put`):
- `API_TOKEN` — auth token (value encrypted, not committed)
- `ADMIN_EMAIL` — admin contact (value encrypted, not committed)

**KV Namespace:**
- Binding: `SETTINGS`
- ID: `02d438ffe49241d19c48f603a209eb0e`
- Stores: `visits` counter (persists across requests and redeploys)

---

## 2. Evidence

### `/health` response
```json
{
  "status": "healthy",
  "timestamp": "2026-05-05T08:59:59.101Z",
  "uptime_ms": 1777971599101
}
```

### `/edge` response (Frankfurt PoP)
```json
{
  "colo": "FRA",
  "country": "DE",
  "city": "Frankfurt am Main",
  "asn": 202053,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3",
  "note": "Served from Cloudflare global edge — no region selection needed"
}
```

### `/counter` response (KV persistence)
```json
{"visits": 2, "stored_by": "edge-api", "persisted": true}
```
Counter survived a full redeploy — KV data is independent of the Worker code.

---

## 3. Global Edge Distribution

Cloudflare Workers runs on **300+ edge locations** worldwide. When a request arrives, Cloudflare's Anycast network routes it to the **nearest PoP** (Point of Presence). The Worker code is replicated globally and executes at that PoP with <5 ms latency from the edge to the user.

**Why there is no "deploy to 3 regions" step:** Cloudflare handles replication automatically. A single `npx wrangler deploy` pushes the Worker to all locations simultaneously. The `colo` field in `/edge` shows which datacenter served the request (`FRA` = Frankfurt).

**Comparison with VM/PaaS:**
- AWS Lambda: you choose `us-east-1`, `eu-west-1`, etc. manually
- Kubernetes: you pick node zones, configure topology spread
- Cloudflare Workers: automatic — just deploy once

---

## 4. Routing Concepts

| Method | Description |
|--------|-------------|
| `workers.dev` | Free subdomain (`edge-api.merkulovlr.workers.dev`). Instant, no DNS config needed. Used here. |
| Routes | Attach a Worker to traffic on a domain you already have in Cloudflare (e.g., `api.example.com/*`). Requires Cloudflare DNS. |
| Custom Domains | Make the Worker the origin for a domain/subdomain. Like Routes but simpler — no zone routing rules needed. |

---

## 5. Observability & Operations

### Logs

```ts
console.log(`[${new Date().toISOString()}] ${request.method} ${url.pathname} from ${request.cf?.colo}`);
```

View live:
```bash
npx wrangler tail
```

Example log entry:
```
[2026-05-05T09:00:00.000Z] GET /edge from FRA
```

### Deployments

```bash
npx wrangler deployments list
```

Multiple versions deployed:
1. `987aee21` — initial deploy
2. `8a897d24` — v1 final (after secrets)
3. `8bfb8833` — v2 (version: 2.0.0 added)
4. Rollback → `8a897d24` restored (verified description reverted)
5. `ec52f743` — v2 redeployed as final

### Rollback

```bash
npx wrangler rollback   # Rolls back to previous deployment
```

Verified: after rollback, `description` field lost v2 text. Redeployed v2 as final.

---

## 6. Kubernetes vs Cloudflare Workers Comparison

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| **Setup complexity** | High — cluster, nodes, networking, ingress | Low — one CLI command |
| **Deployment speed** | Minutes (image pull, pod scheduling) | Seconds (10-12s deploy) |
| **Global distribution** | Manual — choose zones, configure topology spread | Automatic — 300+ PoPs |
| **Cost (small apps)** | ~$100+/mo (managed K8s cluster) | Free tier: 100k req/day |
| **State/persistence** | PVC, StatefulSets, external DBs | KV, D1, R2, Durable Objects |
| **Control/flexibility** | Full control — any language, any binary | Limited runtime (V8 isolates, no sockets, 10ms CPU limit) |
| **Best use case** | Complex stateful microservices, legacy apps | Lightweight APIs, edge logic, global distribution |

### When to Use Kubernetes

- Long-running stateful services (databases, queues)
- Workloads needing >10ms CPU execution
- Complex inter-service communication
- Custom networking (VPNs, sidecars)
- Full container control, custom runtimes

### When to Use Cloudflare Workers

- Globally distributed APIs with low latency requirements
- Auth middleware, URL routing, A/B testing
- Static content transformation
- Rate limiting and bot protection
- Apps where cold-start time matters

### Recommendation

Use **Workers** for lightweight, globally-distributed stateless APIs. Use **Kubernetes** when you need stateful workloads, complex dependencies, or runtime flexibility. They complement each other: K8s for the backend, Workers as the edge layer.

---

## 7. Reflection

**What felt easier than Kubernetes:**
- Deployment is one command with no YAML manifests
- Global distribution is automatic — no topology planning
- Secrets management is simpler (`wrangler secret put`)
- Public URL is instant (`workers.dev`)

**What felt more constrained:**
- No persistent filesystem (KV is eventual-consistency, not POSIX)
- CPU time limit (10ms per request by default)
- V8 isolate runtime — no native modules, no sockets, no `os` module
- No long-running background tasks

**What changed because Workers is not a Docker host:**
- Can't `COPY app.py` — had to rewrite in TypeScript for the Workers runtime
- No Python, no Flask, no `fcntl` — different programming model entirely
- Visit counter uses KV store instead of a file on disk
- No custom port — all requests on port 443 via Cloudflare
