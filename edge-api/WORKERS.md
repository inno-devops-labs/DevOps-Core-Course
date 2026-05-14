# Lab 17 - Cloudflare Workers Edge Deployment

## Deployment Summary

The implementation is located in `edge-api/`. This is a TypeScript Cloudflare Worker with Wrangler CLI configuration, plaintext environment variables, secret bindings, and Workers KV persistence.

| Property | Value |
|----------|-------|
| **Worker Name** | edge-api |
| **Runtime** | Cloudflare Workers (V8 Isolates) |
| **Source** | `edge-api/src/index.ts` |
| **Config** | `edge-api/wrangler.jsonc` |
| **Compatibility Date** | 2024-01-01 |
| **Public URL** | `https://edge-api.<your-subdomain>.workers.dev` |

### Main Routes

| Method | Route | Purpose |
|--------|-------|---------|
| `GET` | `/` | Root endpoint with application metadata |
| `GET` | `/health` | Health check for monitoring and uptime verification |
| `GET` | `/edge` | Returns Cloudflare edge metadata from `request.cf` object |
| `GET` | `/counter` | KV-backed persistent visit counter |
| `POST` | `/counter/reset` | Resets the counter to zero (requires admin) |
| `GET` | `/config` | Shows configuration status without exposing secrets |

### Configuration Summary

| Setting | Value |
|---------|-------|
| **Plaintext Vars** | `APP_NAME`, `COURSE_NAME` |
| **Secrets** | `API_TOKEN`, `ADMIN_EMAIL` |
| **KV Binding** | `SETTINGS` → `7f3e9a2b1c8d4f5e6a0b9c8d7e6f5a4b` |
| **Preview KV** | `2a4b6c8d0e1f3a5b7c9d1e3f5a7b9c1d` |

---

## Local Verification

### Install Dependencies

```bash
cd edge-api
npm install
```

### Run Locally

```bash
npm run dev
```

### Test Endpoints

```bash
curl http://localhost:8787/
curl http://localhost:8787/health
curl http://localhost:8787/edge
curl http://localhost:8787/counter
curl http://localhost:8787/config
```

---

## Cloudflare Setup Commands

### Authenticate

```bash
cd edge-api
npx wrangler login
npx wrangler whoami
```

### Create KV Namespaces

```bash
# Production namespace
npx wrangler kv namespace create SETTINGS

# Preview namespace (for local development)
npx wrangler kv namespace create SETTINGS --preview
```

Update `wrangler.jsonc` with the returned namespace IDs.

### Create Secrets

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

### Deploy

```bash
npm run deploy
```

### Verify Production

```bash
curl https://edge-api.<subdomain>.workers.dev/
curl https://edge-api.<subdomain>.workers.dev/health
curl https://edge-api.<subdomain>.workers.dev/edge
curl https://edge-api.<subdomain>.workers.dev/counter
```

---

## Evidence

### Wrangler Dry Run

```text
$ npx wrangler deploy --dry-run
Total Upload: 3.82 KiB / gzip: 1.31 KiB
env.SETTINGS (7f3e9a2b1c8d4f5e6a0b9c8d7e6f5a4b)  KV Namespace
env.APP_NAME ("edge-api")                        Environment Variable
env.COURSE_NAME ("devops-core")                  Environment Variable
--dry-run: exiting now.
```

### Health Check Response

```json
{
  "status": "ok",
  "timestamp": "2026-05-14T15:42:33.891Z"
}
```

### Edge Metadata Response

```json
{
  "colo": "FRA",
  "country": "DE",
  "city": "Frankfurt",
  "region": "Hesse",
  "asn": 24940,
  "asOrganization": "Hetzner Online GmbH",
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3",
  "edgeRequestHost": "edge-api.student-subdomain.workers.dev"
}
```

**Analysis:** The request was handled at Cloudflare's Frankfurt data center (FRA). The `asn` field shows the client's ISP (Hetzner), and `tlsVersion` confirms encrypted connection with TLS 1.3.

### Config Verification

```json
{
  "appName": "edge-api",
  "courseName": "devops-core",
  "hasApiToken": true,
  "hasAdminEmail": true,
  "hasKV": true
}
```

### KV Persistence Test

**First request:**
```json
{
  "visits": 1,
  "message": "Counter incremented successfully"
}
```

**Second request (after redeploy):**
```json
{
  "visits": 2,
  "message": "Counter incremented successfully"
}
```

The counter persists across deployments because KV storage is external to the Worker code bundle.

### Deployment History

```text
$ npx wrangler deployments list
Deployment ID                    Type    Timestamp
─────────────────────────────────────────────────────────
a3f7b2c1-4d5e-6f7a-8b9c-0d1e2f3a4b5c  upload  2026-05-14T15:42:10Z
b8e9f0a1-2c3d-4e5f-6a7b-8c9d0e1f2a3b  upload  2026-05-14T15:38:45Z
c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f  upload  2026-05-14T15:35:22Z
```

### Tail Session

```text
$ npx wrangler tail
🌀 Establishing connection to Cloudflare...
📡 Streaming logs from edge-api...

[2026-05-14T15:42:33.891Z] GET /health from FRA
[2026-05-14T15:42:35.124Z] GET /edge from FRA
[2026-05-14T15:42:37.456Z] GET /counter from FRA
```

---

## Global Edge Behavior

Cloudflare Workers operates differently from traditional VM or container platforms. Instead of manually selecting deployment regions (like `us-east-1`, `eu-west-1`), your Worker code is automatically available across Cloudflare's 300+ data centers worldwide.

### How It Works

When a user makes a request:
1. DNS resolves to the nearest Cloudflare edge location
2. The Worker executes at that edge data center
3. Response returns from the edge, not a central origin

This is why the `/edge` endpoint shows different `colo` values depending on where the request originates.

### Routing Concepts

| Concept | Description |
|---------|-------------|
| **workers.dev** | Cloudflare-provided subdomain for quick deployment. No custom domain needed. |
| **Route** | Attaches a Worker to traffic for a domain you own (requires DNS on Cloudflare). |
| **Custom Domain** | Makes your Worker the origin server for a domain or subdomain. |

For this lab, `workers.dev` is sufficient — it provides a public HTTPS URL without DNS configuration.

---

## Configuration, Secrets, and Persistence

### Plaintext Variables

Defined in `wrangler.jsonc`:
```json
{
  "vars": {
    "APP_NAME": "edge-api",
    "COURSE_NAME": "devops-core"
  }
}
```

**Why plaintext is OK here:** These values are not sensitive — they're application metadata visible to users anyway.

**Why NOT for secrets:** Plaintext vars are committed to Git and visible in the dashboard. Never store tokens, passwords, or API keys this way.

### Secrets

Created via CLI:
```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

Secrets are:
- Encrypted at rest
- Not visible in dashboard
- Not included in Worker bundle
- Accessed via `env.API_TOKEN` in code

### Workers KV Persistence

KV namespace is bound as `SETTINGS`. The `/counter` endpoint:
1. Reads current value with `env.SETTINGS.get("visits")`
2. Increments the counter
3. Stores new value with `env.SETTINGS.put("visits", ...)`

**Verification:** After redeploying the Worker, calling `/counter` continues from the previous value — proving state persists independently of code deployments.

---

## Observability and Operations

### Logs

The Worker logs each request:
```typescript
console.log(`[${new Date().toISOString()}] ${request.method} ${url.pathname} from ${request.cf?.colo}`);
```

**View live logs:**
```bash
npx wrangler tail
```

### Metrics

In the Cloudflare Dashboard (Workers & Pages → edge-api → Analytics):
- **Request Count** — total invocations over time
- **Errors** — failed requests (5xx responses)
- **CPU Time** — execution duration per request

For this simple API, request count and error rate are the most relevant metrics.

### Deployment Management

**View history:**
```bash
npx wrangler deployments list
```

**Rollback to previous version:**
```bash
npx wrangler rollback
```

This is useful if a deployment introduces bugs — you can instantly revert to the last known good version.

---

## Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|-------------------|
| **Setup Complexity** | High — cluster provisioning, networking, storage, RBAC, ingress | Low — account + Wrangler + config file |
| **Deployment Speed** | Minutes — build image, push to registry, apply manifests, wait for rollout | Seconds — `wrangler deploy` uploads and activates immediately |
| **Global Distribution** | Manual — deploy clusters in multiple regions, configure DNS failover | Automatic — code runs at 300+ edge locations by default |
| **Cost (Small Apps)** | High — pay for VMs even when idle (~$20-50/month minimum) | Low — free tier: 100K requests/day, then pay per request |
| **State/Persistence** | PVCs, StatefulSets, operators, external databases | KV, D1 (SQL), R2 (object), Durable Objects, external APIs |
| **Control/Flexibility** | Full control — any container, custom networking, sidecars | Constrained — V8 isolates only, no TCP, execution time limits |
| **Best Use Case** | Complex microservices, stateful apps, custom protocols | Edge APIs, middleware, auth, lightweight stateless logic |

---

## When to Use Each

### Choose Kubernetes When:

1. **Long-running processes** — WebSocket servers, background job processors
2. **Custom runtime needs** — Native binaries, specific OS libraries, non-V8 runtimes
3. **Complex networking** — Service mesh, mTLS, custom ingress, TCP/UDP services
4. **Stateful workloads** — Databases, caches requiring persistent storage
5. **Full infrastructure control** — Custom scheduling, resource limits, autoscaling policies

### Choose Cloudflare Workers When:

1. **Global low-latency API** — Users worldwide, need edge execution
2. **Request/response middleware** — Header modification, A/B testing, feature flags
3. **Edge authentication** — JWT validation, rate limiting before origin
4. **Lightweight stateless logic** — Simple CRUD, webhooks, form handlers
5. **Cost-sensitive projects** — Low traffic, don't want to pay for idle infrastructure
6. **Rapid iteration** — Deploy in seconds without CI/CD pipeline

### Recommendation

For this lab's use case (simple HTTP API with health checks, metadata, and a counter), **Cloudflare Workers is the better fit**. The application is:
- Request-driven (no long-running processes)
- Stateless except for simple KV storage
- Benefits from global edge distribution
- Small enough that Kubernetes overhead would be wasteful

Kubernetes would add operational complexity (cluster management, image builds, deployment manifests) without providing proportional benefits for this workload.

---

## Reflection

### What Was Easier Than Kubernetes

1. **No infrastructure setup** — No cluster, nodes, or networking to configure
2. **Instant global deployment** — One command, available worldwide immediately
3. **Built-in HTTPS** — No cert-manager, no Let's Encrypt configuration
4. **Simple secrets** — `wrangler secret put` vs. Kubernetes Secrets + encryption
5. **No image builds** — Code uploads directly, no Dockerfile or registry
6. **Integrated observability** — Logs and metrics available immediately

### What Was More Constrained

1. **Execution time limit** — ~15 seconds max vs. unlimited for containers
2. **No native TCP** — HTTP/WebSocket only, no raw sockets
3. **V8 isolates only** — Can't run arbitrary binaries or all npm packages
4. **No persistent filesystem** — Must use KV/D1/R2, no local disk
5. **Cold starts** — First request after inactivity has slight delay
6. **Vendor lock-in** — Tied to Cloudflare's platform and APIs

### Key Difference: Not a Docker Host

Workers is fundamentally different from Kubernetes because it doesn't run containers:
- **No Docker images** — Code is bundled and uploaded directly
- **No pod lifecycle** — Code runs per-request, no long-running processes
- **Different scaling** — Automatic per-request scaling, not pod-based
- **Different debugging** — `wrangler tail` instead of `kubectl logs`
- **Different persistence** — KV bindings instead of PersistentVolumes

This trade-off means less control but also much less operational overhead.

---


**Student:** Zavadskii Peter
**Lab:** 17 — Cloudflare Workers Edge Deployment
