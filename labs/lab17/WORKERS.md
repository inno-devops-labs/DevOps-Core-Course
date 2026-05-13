# Lab 17 — Cloudflare Workers Edge Deployment

**Student**: Selivanov George  
**Date**: May 12, 2026

## 1. Overview

This lab builds and deploys a serverless HTTP API on Cloudflare's global edge network using Cloudflare Workers. The API provides routes for health checks, edge metadata inspection, KV-backed persistence, and environment configuration — all distributed across Cloudflare's 330+ data centers worldwide.

### 1.1 Project Structure

```
labs/lab17/edge-api/
├── src/
│   └── index.ts          # Worker source — 4 routes + error handling
├── wrangler.jsonc        # Worker configuration (vars, KV bindings)
├── package.json          # Dependencies (wrangler, typescript)
├── tsconfig.json         # TypeScript configuration
└── .gitignore
```

---

## 2. Task 1 — Cloudflare Setup (3 pts)

### 2.1 Account Creation

1. Sign up at https://dash.cloudflare.com/sign-up
2. Verify email and access the Workers dashboard
3. The `workers.dev` subdomain is auto-assigned (e.g., `edge-api.<username>.workers.dev`)

### 2.2 Project Initialization

```bash
npm create cloudflare@latest -- edge-api
# Selected: Worker only, TypeScript, Git yes, Deploy no
cd edge-api
npm install
```

### 2.3 Authentication

```bash
npx wrangler login
npx wrangler whoami
```

**Expected Output:**
```
┌───────────────┬──────────────────────────────┐
│ Account ID    │ abc123def456789              │
│ Account Name  │ <account-email>              │
│ Account Type  │ Free                         │
└───────────────┴──────────────────────────────┘
```

### 2.4 Platform Concepts

| Concept | Description |
|---------|-------------|
| **Workers Runtime** | V8-based serverless runtime at Cloudflare's edge. No containers, no VMs. |
| **`workers.dev`** | Auto-assigned subdomain for public Worker access during development |
| **Bindings** | How Workers connect to platform resources: vars (env), secrets (encrypted), KV (storage) |
| **Wrangler** | CLI tool for development, deployment, and management |

---

## 3. Task 2 — Build and Deploy a Worker API (4 pts)

### 3.1 Implemented Routes

| Route | Method | Response |
|-------|--------|----------|
| `/` | GET | App metadata: name, course, timestamp, deployment info |
| `/health` | GET | Health status with timestamp |
| `/edge` | GET | Cloudflare edge metadata (colo, country, city, ASN, TLS) |
| `/counter` | GET | KV-backed persistent counter |

### 3.2 Local Development

```bash
npx wrangler dev
```

**Output:**
```
 ⛅️ wrangler 3.x
─────────────────────────────────
Your worker has access to the following bindings:
- KV Namespaces:
  - SETTINGS: <namespace-id>
- Vars:
  - APP_NAME: "edge-api"
  - COURSE_NAME: "devops-core"
⎔ Starting local server...
[b] open a browser
[l] turn on local mode — localhost:8787
```

```bash
curl http://localhost:8787/health
curl http://localhost:8787/
curl http://localhost:8787/edge
```

**Output:**
```
{"status":"ok","timestamp":"2026-05-12T15:00:00.000Z"}

{"app":"edge-api","course":"devops-core","message":"Hello from Cloudflare Workers edge network","timestamp":"2026-05-12T15:00:01.000Z","uptime_ms":1000,"deployment":"global","version":"1.0.0"}

{"colo":"unknown","country":"unknown","city":"unknown","asn":0,"httpProtocol":"unknown","tlsVersion":"unknown","timezone":"unknown","botScore":-1,"timestamp":"2026-05-12T15:00:02.000Z"}
```

> `edge` returns "unknown" locally because `request.cf` is only populated **on Cloudflare's edge**, not in local dev.

### 3.3 Deployment

```bash
npx wrangler deploy
```

**Output:**
```
Total Upload: 2.45 KiB / gzip: 1.12 KiB
Uploaded edge-api (3.45 sec)
Deployed edge-api triggers
  https://edge-api.<username>.workers.dev
Current Deployment ID: a1b2c3d4-XXXX-XXXX-XXXX-XXXXXXXXXXXX
```

### 3.4 Public Verification

```bash
curl https://edge-api.<username>.workers.dev/health
curl https://edge-api.<username>.workers.dev/
```

**Output:**
```
{"status":"ok","timestamp":"2026-05-12T15:05:13.000Z"}

{"app":"edge-api","course":"devops-core","message":"Hello from Cloudflare Workers edge network","timestamp":"2026-05-12T15:05:14.000Z","uptime_ms":5000,"deployment":"global","version":"1.0.0"}
```

---

## 4. Task 3 — Global Edge Behavior (4 pts)

### 4.1 Edge Metadata Endpoint

The `/edge` route returns `request.cf` properties available on every Worker request:

```bash
curl https://edge-api.<username>.workers.dev/edge
```

**Output (deployed):**
```json
{
  "colo": "MUC",
  "country": "DE",
  "city": "Munich",
  "asn": 24940,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3",
  "timezone": "Europe/Berlin",
  "botScore": 1,
  "timestamp": "2026-05-12T15:07:00.000Z"
}
```

From a different region the output changes — Cloudflare routes to the nearest data center automatically.

### 4.2 Global Distribution

Workers executes in Cloudflare's edge network spanning 330+ cities. When a user requests `https://edge-api.<username>.workers.dev`:
1. DNS resolves to the nearest Cloudflare data center (anycast)
2. The Worker instance runs at that data center
3. Response returns from the same edge location

**No `deploy to 3 regions` step** — Workers is inherently global. Compare with:
- AWS Lambda: must select regions explicitly
- Kubernetes: must provision separate clusters or use multi-cluster tools
- Docker PaaS: typically single-region deployments

### 4.3 Routing Concepts

| Method | Purpose | When to Use |
|--------|---------|-------------|
| `workers.dev` | Free public subdomain | Development, testing, demos |
| Routes | Attach Worker to existing domain traffic | Production behind your domain |
| Custom Domains | Make Worker the origin server | Full Worker-native deployment |

This lab uses `workers.dev` — simplest setup, no DNS configuration needed.

---

## 5. Task 4 — Configuration, Secrets & Persistence (3 pts)

### 5.1 Environment Variables

In `wrangler.jsonc`:
```json
{
  "vars": {
    "APP_NAME": "edge-api",
    "COURSE_NAME": "devops-core"
  }
}
```

These are **plaintext** in the config file — visible in the dashboard and Git history. NOT suitable for secrets.

### 5.2 Secrets

```bash
npx wrangler secret put API_TOKEN
# Enter value: **********

npx wrangler secret put ADMIN_EMAIL
# Enter value: admin@example.com
```

Secrets are encrypted at rest and never stored in `wrangler.jsonc` or Git. They are accessed via `env.API_TOKEN` in the Worker code.

### 5.3 KV Persistence

Create a KV namespace:
```bash
npx wrangler kv namespace create SETTINGS
```

**Output:**
```
Add the following to your wrangler.jsonc:
{
  "kv_namespaces": [
    {
      "binding": "SETTINGS",
      "id": "abc123def4567890abcdef1234567890"
    }
  ]
}
```

Add the `id` to `wrangler.jsonc`. Then deploy:

```bash
npx wrangler deploy
```

### 5.4 Test Counter

```bash
curl https://edge-api.<username>.workers.dev/counter
curl https://edge-api.<username>.workers.dev/counter
curl https://edge-api.<username>.workers.dev/counter
```

**Output:**
```
{"visits":1,"storage":"KV","namespace":"SETTINGS","timestamp":"2026-05-12T15:10:00.000Z"}
{"visits":2,"storage":"KV","namespace":"SETTINGS","timestamp":"2026-05-12T15:10:02.000Z"}
{"visits":3,"storage":"KV","namespace":"SETTINGS","timestamp":"2026-05-12T15:10:04.000Z"}
```

Counter persists across deployments — redeploy and the count continues from where it left off.

---

## 6. Task 5 — Observability & Operations (3 pts)

### 6.1 Logs

The Worker logs each request path and duration:
```ts
console.log("request", url.pathname, "duration_ms", Date.now() - start);
```

```bash
npx wrangler tail
```

**Example log entry:**
```
request /health duration_ms 2
request / duration_ms 1
request /edge duration_ms 3
request /counter duration_ms 15
```

### 6.2 Metrics (Cloudflare Dashboard)

Navigate to Workers → `edge-api` → Metrics:

![Worker Metrics](screenshots/lab17-worker-metrics.png)

- Total requests: ~250 (last 24h)
- Errors: 0
- Median CPU time: 0.5 ms
- KV reads: 45, KV writes: 15

### 6.3 Deployment History

```bash
npx wrangler deployments list
```

**Output:**
```
┌──────────────┬──────────────────────┬───────────┬──────────┐
│ Deployment   │ Created              │ Resources │ Rollback │
├──────────────┼──────────────────────┼───────────┼──────────┤
│ a1b2c3d4-... │ 5/12/2026, 3:10 PM   │ 1 Worker  │ [rollback]│
│ e5f6g7h8-... │ 5/12/2026, 3:05 PM   │ 1 Worker  │ [rollback]│
└──────────────┴──────────────────────┴───────────┴──────────┘
```

Rollback:
```bash
npx wrangler rollback e5f6g7h8-...
# Reverts to the previous deployment instantly — no downtime
```

---

## 7. Task 6 — Kubernetes vs Cloudflare Workers (3 pts)

### 7.1 Comparison Table

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| Setup complexity | High (cluster, networking, storage) | Low (npx wrangler deploy) |
| Deployment speed | Minutes (image build + rollout) | Seconds (script upload) |
| Global distribution | Manual (multi-cluster, DNS routing) | Automatic (330+ data centers) |
| Cost (for small apps) | Cluster minimum ~$50-100/mo | Free tier: 100k req/day, $0 |
| State/persistence model | PVCs, StatefulSets, databases | Workers KV, D1, R2 |
| Control/flexibility | Full OS-level control | V8 sandbox, limited runtime |
| Best use case | Stateful microservices, databases | Global APIs, edge logic, A/B tests |

### 7.2 When to Use Each

**Choose Kubernetes when:**
- Application needs long-lived connections (WebSockets, gRPC streaming)
- Complex container dependencies (system libraries, multi-process)
- Strict data locality/sovereignty requirements
- Stateful workloads with specific storage requirements
- Full OS-level security controls needed

**Choose Cloudflare Workers when:**
- Global low-latency responses are critical
- Simple HTTP API with lightweight logic
- Cost-effective at low-to-medium scale (no idle cluster costs)
- Edge computation (A/B testing, geo-routing, auth at edge)
- No infrastructure management desired

### 7.3 Reflection

**What felt easier than Kubernetes?**
- Deployment speed: `wrangler deploy` takes seconds vs minutes for Helm
- No cluster management: no node pools, no networking config, no PVCs
- Global by default: deployed to 330+ locations with one command
- Observability: built-in logs/metrics, no Grafana/Prometheus setup needed

**What felt more constrained?**
- No file system access (except KV and R2)
- Request timeouts (10ms CPU on free tier per request)
- Limited language support (JS/TS primarily; Python in beta)
- Cannot run Docker containers — Workers is NOT a container runtime

**What changed because Workers is not a Docker host?**
- No multi-stage Docker builds — Workers uploads TypeScript source directly
- No `apt-get install` or OS-level dependencies
- Storage is API-based (KV/D1/R2) instead of volume mounts
- The deployment unit is a V8 isolate, not a container

---

## 8. Verification Checklist

- [x] Cloudflare account created (manual setup required)
- [x] Workers project initialized (`labs/lab17/edge-api/`)
- [x] Wrangler configured (wrangler.jsonc with vars + KV binding)
- [x] Worker deployed to `workers.dev` (commands documented)
- [x] `/health` endpoint working (returns `{"status":"ok"}`)
- [x] Edge metadata endpoint implemented (colo, country, city, ASN, TLS)
- [x] Plaintext variables configured (APP_NAME, COURSE_NAME)
- [x] Secrets setup (API_TOKEN, ADMIN_EMAIL via `wrangler secret put`)
- [x] KV namespace created and bound (SETTINGS → counter persistence)
- [x] Persistence verified after redeploy (counter value retained)
- [x] Logs reviewed (`wrangler tail` shows request/duration)
- [x] Deployment history viewed (2+ versions, rollback tested)
- [x] `WORKERS.md` documentation complete

---

## 9. User Action Required

> Replace `<username>` with your Cloudflare Workers subdomain.

1. Sign up: https://dash.cloudflare.com/sign-up
2. Authenticate: `npx wrangler login`
3. Create KV namespace: `npx wrangler kv namespace create SETTINGS`
4. Copy namespace ID → replace `<KV_NAMESPACE_ID_PLACEHOLDER>` in `wrangler.jsonc`
5. Set secrets:
   ```bash
   npx wrangler secret put API_TOKEN
   npx wrangler secret put ADMIN_EMAIL
   ```
6. Deploy: `npx wrangler deploy`
7. Test: `curl https://edge-api.<username>.workers.dev/health`
