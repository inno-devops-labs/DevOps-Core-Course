# Lab 17 — Cloudflare Workers Edge Deployment

## 1. Setup

### Installation & Authentication

```bash
npm create cloudflare@latest -- edge-api
cd edge-api
npx wrangler login
npx wrangler whoami
```

![wrangler whoami output](../k8s/img/lab17/wrangler-whoami.png)

### Platform Concepts

| Concept | Description |
|---------|-------------|
| **Workers runtime** | Lightweight V8-based isolate, not a container or VM. Starts in <1ms. Runs at the edge, not in a fixed region. |
| **`workers.dev` URL** | Every Worker gets a free public URL: `https://<name>.<subdomain>.workers.dev` |
| **Bindings** | How Workers access platform resources: `vars` (plaintext), `secrets` (encrypted), `KVNamespace` (key-value store) |
| **Wrangler** | CLI tool for development, deployment, secrets, logs, and rollbacks |

---

## 2. Worker API

### Routes Implemented

| Endpoint | Description |
|----------|-------------|
| `GET /` | App info: name, course, timestamp |
| `GET /health` | `{"status": "ok"}` |
| `GET /edge` | Edge metadata: colo, country, city, ASN, protocol, TLS |
| `GET /counter` | KV-backed visit counter, increments on each request |
| `GET /info` | Config info: app name, admin email, available routes |

### Local Development

```bash
cd edge-api
npm install
npx wrangler dev
```

![wrangler dev — local server running on localhost:8787](../k8s/img/lab17/wrangler-dev.png)

Test locally:

```bash
curl http://localhost:8787/health
curl http://localhost:8787/
curl http://localhost:8787/edge
```

![curl responses from local worker](../k8s/img/lab17/local-test.png)

### Deploy

```bash
npx wrangler deploy
```

![wrangler deploy output — Worker URL](../k8s/img/lab17/wrangler-deploy.png)

**Worker URL:** `https://edge-api.arina-zimina.workers.dev`

Verify deployed Worker:

```bash
curl https://edge-api.arina-zimina.workers.dev/health
curl https://edge-api.arina-zimina.workers.dev/
```

![Deployed Worker responding in browser](../k8s/img/lab17/worker-running.png)

---

## 3. Global Edge Behavior

### Edge Metadata Endpoint

```bash
curl https://edge-api.arina-zimina.workers.dev/edge
```

Example response:

```json
{
  "colo": "AMS",
  "country": "RU",
  "city": "Innopolis",
  "asn": 12345,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3"
}
```

![/edge JSON response showing colo and country](../k8s/img/lab17/edge-metadata.png)

### How Workers Distributes Globally

Cloudflare Workers runs on 300+ edge locations worldwide. When a request arrives, Cloudflare's Anycast network routes it to the **nearest data center** (`colo` in the response). The Worker code is deployed to **all locations simultaneously** — there is no concept of "deploy to 3 regions" because the code is everywhere by default.

Compare with VM/PaaS platforms:
- **Kubernetes**: you must create clusters in each region, configure ingress, manage cross-region routing
- **Fly.io/Heroku**: you choose specific regions and scale machines in them manually
- **Workers**: `npx wrangler deploy` → available in 300+ locations instantly, no configuration

### Routing Concepts

| Mechanism | How it works |
|-----------|-------------|
| `workers.dev` | Free subdomain, enabled by default, no DNS config needed |
| Routes | Attach Worker to traffic on your Cloudflare zone (e.g., `api.yourdomain.com/*`) |
| Custom Domains | Make the Worker the origin for a specific domain or subdomain |

`workers.dev` is used for this lab — no custom domain required.

---

## 4. Configuration, Secrets & Persistence

### Environment Variables

Defined in `wrangler.jsonc`:

```json
"vars": {
  "APP_NAME": "devops-info-service",
  "COURSE_NAME": "devops-core"
}
```

Plaintext vars are **not suitable for secrets** because they are committed to Git and visible in the Cloudflare dashboard to anyone with access. Secrets are encrypted at rest and never exposed in logs or config files.

### Secrets

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

![wrangler secret put prompts](../k8s/img/lab17/secrets-set.png)

Secrets are injected as environment variables at runtime. Values are never stored in `wrangler.jsonc` or Git.

### Workers KV

```bash
npx wrangler kv namespace create SETTINGS
```

Copy the returned `id` into `wrangler.jsonc` under `kv_namespaces`.

```bash
npx wrangler deploy
curl https://edge-api.arina-zimina.workers.dev/counter
# {"visits": 1}
curl https://edge-api.arina-zimina.workers.dev/counter
# {"visits": 2}
```

![KV counter incrementing across requests](../k8s/img/lab17/kv-counter.png)

**Persistence verification after redeploy:**

```bash
curl https://edge-api.arina-zimina.workers.dev/counter
# {"visits": N}
npx wrangler deploy   # redeploy
curl https://edge-api.arina-zimina.workers.dev/counter
# {"visits": N+1}   ← value survived redeploy
```

KV data is stored in Cloudflare's global key-value store, not in the Worker process — it persists across redeployments and cold starts.

---

## 5. Observability & Operations

### Logs

```bash
npx wrangler tail
```

In a second terminal, make a request:

```bash
curl https://edge-api.arina-zimina.workers.dev/edge
```

![wrangler tail — live log entry with path and colo](../k8s/img/lab17/wrangler-tail.png)

### Dashboard Metrics

Open **https://dash.cloudflare.com** → Workers & Pages → `edge-api` → **Metrics tab**

![Cloudflare dashboard metrics — requests and CPU time](../k8s/img/lab17/dashboard-metrics.png)

### Deployment History & Rollback

```bash
# Deploy v1
npx wrangler deploy

# Make a change (e.g., update APP_NAME in wrangler.jsonc)
npx wrangler deploy

# View history
npx wrangler deployments list
```

![wrangler deployments list](../k8s/img/lab17/deployments-list.png)

```bash
# Rollback to previous version
npx wrangler rollback
```

![wrangler rollback confirmation](../k8s/img/lab17/rollback.png)

---

## 6. Kubernetes vs Cloudflare Workers Comparison

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| **Setup complexity** | High — cluster, namespaces, RBAC, ingress | Minimal — `npm create cloudflare` and done |
| **Deployment speed** | Minutes (image pull, pod scheduling) | Seconds — global rollout in ~2s |
| **Global distribution** | Manual — multi-cluster federation | Automatic — 300+ locations instantly |
| **Cost (small apps)** | Medium — nodes run 24/7 | Free tier: 100k req/day, paid: $5/10M req |
| **State/persistence** | PVC, StatefulSets, external DBs | KV (eventually consistent), Durable Objects (strongly consistent) |
| **Control/flexibility** | Maximum — full OS, any runtime | Limited — V8 isolate, no arbitrary binaries |
| **Best use case** | Complex microservices, stateful workloads | Lightweight APIs, edge logic, globally distributed handlers |

### When to Use Kubernetes

- Complex microservices with many interdependent services
- Stateful workloads requiring fine-grained storage control (StatefulSets, PVCs)
- Long-running compute tasks exceeding Workers' 30s CPU time limit
- Need for custom operators, CRDs, or advanced scheduling
- Full infrastructure ownership required (compliance, on-prem)

### When to Use Cloudflare Workers

- Globally distributed APIs with low-latency requirements
- Lightweight edge logic: auth, routing, A/B testing, rate limiting
- Apps that need to be globally available without infrastructure management
- Cost-sensitive projects with bursty or unpredictable traffic
- Prototypes needing instant public URLs

### Recommendation

For the DevOps Info Service as a public API — **Workers is the better fit**. The app is stateless, simple, and benefits from global edge execution. Workers provides HTTPS, instant global deployment, and a built-in `/workers.dev` URL with zero infrastructure management. The only compromise is the Workers runtime constraint (no arbitrary system calls), but this app has no such requirements. Kubernetes would be chosen only if the service became part of a larger microservices ecosystem requiring shared networking with other cluster workloads.

### Reflection

**What felt easier than Kubernetes:**
- No cluster to manage, no YAML manifests, no `kubectl` debugging
- `npx wrangler deploy` deploys globally in seconds vs minutes for a Kubernetes rolling update
- Secrets management is a single CLI command vs Kubernetes Secrets + RBAC configuration
- Logs are instantly accessible via `wrangler tail` vs multi-step Grafana/Loki setup

**What felt more constrained:**
- No Docker — cannot reuse the existing image from Lab 2
- Worker runtime limits (30s CPU time, 128MB memory) would block heavy workloads
- KV is eventually consistent — not suitable for strict ACID requirements
- Cannot run background processes or long-lived connections

**What changed because Workers is not a Docker host:**
- Had to rewrite the app in TypeScript (Workers runtime); the Python Flask app cannot run here
- Persistence model changed: files and SQLite are replaced by KV namespaces and Durable Objects
- Health checks are just HTTP routes — no liveness/readiness probes or pod restart logic
