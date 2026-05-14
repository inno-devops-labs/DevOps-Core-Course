# Lab 17 — Cloudflare Workers Edge Deployment

## 1. Deployment Summary

**Worker URL:** `https://edge-api.tsixphoenix.workers.dev`

**Routes:**

| Path | Description |
|------|-------------|
| `/` | App info: name, course, timestamp |
| `/health` | Health check — always `{ "status": "ok" }` |
| `/edge` | Edge metadata from `request.cf`: colo, country, city, ASN, protocol, TLS |
| `/counter` | KV-backed visit counter, persists across deploys |
| `/info` | App config: env vars, admin email, route list |

**Config:**
- Plaintext vars: `APP_NAME=edge-api`, `COURSE_NAME=devops-core`
- Secrets: `API_TOKEN`, `ADMIN_EMAIL` (set via `wrangler secret put`, not in git)
- KV namespace `SETTINGS` bound for counter persistence

---

## 2. Evidence

### Cloudflare Dashboard

<!-- Replace with your screenshot -->
![Cloudflare Workers Dashboard](img/dashboard.png)

### `/edge` JSON response

```json
{
  "colo": "AMS",
  "country": "NL",
  "city": "Amsterdam",
  "asn": 41111,
  "httpProtocol": "HTTP/1.1",
  "tlsVersion": "TLSv1.2"
}
```

<!-- Replace with your actual curl output or screenshot -->
![Edge response](img/edge-response.png)

### Deployment history (`wrangler deployments list`)

7 deployments were made during lab setup (code deploys + secret rotations):

```
Version cbdac941  2026-05-14T15:05:34Z  Upload  (v1 — initial code)
Version 506f3bdf  2026-05-14T15:08:58Z  Upload  (v2 — added "version" field to / response)
```

Rollback command: `npx wrangler rollback` (rolls back to previous version).

### Logs / Metrics

<!-- Replace with wrangler tail or dashboard metrics screenshot -->
![Logs](img/logs.png)

Console log added in worker (`console.log("request", method, pathname, "colo", colo)`).
View live with: `npx wrangler tail`

---

## 3. Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| Setup complexity | High — cluster, nodes, namespaces, Helm | Low — `npm create`, `wrangler deploy` |
| Deployment speed | Minutes (image build + rollout) | Seconds (edge push) |
| Global distribution | Manual — choose regions, replicate | Automatic — 300+ PoPs, no config |
| Cost (small apps) | Non-trivial — compute even at idle | Free tier generous (100k req/day) |
| State/persistence model | PVCs, StatefulSets, external DBs | KV, Durable Objects, D1 (edge-native) |
| Control/flexibility | Full — any runtime, any port, stateful | Limited — V8 isolates, no sockets, 128 MB RAM |
| Best use case | Long-running services, complex workloads | Lightweight APIs, routing, auth at edge |

---

## 4. When to Use Each

**Kubernetes shines when:**
- You run stateful services (databases, queues)
- You need long-running processes or background workers
- You have complex inter-service communication
- You need full OS-level control or custom runtimes (JVM, Go, Python)

**Cloudflare Workers shines when:**
- You need a globally fast, lightweight HTTP API
- Cold start must be zero (isolates vs containers)
- You want zero infra management
- Use cases: API gateways, auth middleware, A/B routing, geo-aware responses

**My recommendation:** Workers for stateless edge APIs, Kubernetes for everything that needs state, long execution, or complex orchestration. They complement each other well — Workers can be the edge layer in front of a K8s cluster.

---

## 5. Reflection

**Easier than Kubernetes:**
- No cluster setup — `wrangler deploy` and you're global
- No YAML manifests for services, ingresses, namespaces
- Logs and metrics built-in to the dashboard
- Rollback is one command: `wrangler rollback`

**More constrained:**
- No persistent TCP connections, no raw sockets
- 128 MB RAM limit, 50 ms CPU time on free tier
- No Docker — Workers runtime is V8 isolates, not containers
- Limited language support (JS/TS/Python/Wasm only)

**What changed because Workers is not a Docker host:**
- The app from Lab 2 (FastAPI/Python in a container) can't run here as-is
- State (DB, files) must use Workers-native primitives: KV, D1, R2
- No `EXPOSE` ports, no `docker-compose` — the platform handles routing entirely

---

## Checklist

- [x] Cloudflare account created
- [x] Workers project initialized (`edge-api`)
- [x] Wrangler authenticated
- [x] Worker deployed to `workers.dev`
- [x] `/health` endpoint working
- [x] Edge metadata endpoint (`/edge`) with colo, country, city, ASN
- [x] Plaintext vars: `APP_NAME`, `COURSE_NAME`
- [x] Secrets: `API_TOKEN`, `ADMIN_EMAIL`
- [x] KV namespace `SETTINGS` created and bound
- [x] Persistence verified: `/counter` increments across deploys
- [x] Logs reviewed via `wrangler tail` / dashboard
- [x] Deployment history: `wrangler deployments list`
- [x] `WORKERS.md` complete
- [x] Kubernetes comparison documented
