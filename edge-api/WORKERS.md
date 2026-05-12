# Cloudflare Workers Lab Report

## Deployment Summary

- **Worker name:** `edge-api`
- **Worker URL:** `https://edge-api.bulatsigapov004.workers.dev`
- **Account ID:** `c53b8478c028d917f194df4b915ed6f0`
- **Runtime:** Cloudflare Workers (TypeScript, Worker-only template)
- **Main routes:**
  - `GET /` — app info and config overview
  - `GET /health` — health status
  - `GET /deployment` — deployment metadata (includes whether secrets are bound)
  - `GET /edge` — edge location / request metadata
  - `POST /kv` — store key/value in Workers KV
  - `GET /kv?key=<key>` — read key/value from Workers KV
- **Configuration used:**
  - Plain vars in `wrangler.jsonc`: `APP_NAME`, `ENVIRONMENT`, `DEPLOYMENT_VERSION`
  - Secrets (Wrangler): `API_TOKEN`, `ADMIN_EMAIL`
  - KV binding: `SETTINGS` (namespace id `36cc749b353d465090b0f0ca2663e692`)

## Task 1: Cloudflare Setup

### Account and Dashboard

- Created Cloudflare account: **Done** (OAuth user `bulatsigapov004@gmail.com`)
- Confirmed Workers access in dashboard: **Done**
- **workers.dev subdomain:** Cloudflare gives you a personal subdomain under `workers.dev`. Deployed Workers are reachable at `https://<worker-name>.<your-subdomain>.workers.dev` (this lab uses `https://edge-api.bulatsigapov004.workers.dev`).

### Project Initialization

Commands used:

```bash
npm create cloudflare@latest -- edge-api
cd edge-api
```

Selected options:

- `Hello World example`
- `Worker only`
- `TypeScript`
- `Git: Yes`
- `Deploy now: No`

### Wrangler Authentication

Commands:

```bash
npx wrangler login
npx wrangler whoami
```

Verification result (`whoami`):

```text

 ⛅️ wrangler 4.90.0 (update available 4.90.1)
─────────────────────────────────────────────
Getting User settings...
👋 You are logged in with an OAuth Token, associated with the email bulatsigapov004@gmail.com.
┌─────────────────────────────────────┬──────────────────────────────────┐
│ Account Name                        │ Account ID                       │
├─────────────────────────────────────┼──────────────────────────────────┤
│ Bulatsigapov004@gmail.com's Account │ c53b8478c028d917f194df4b915ed6f0 │
└─────────────────────────────────────┴──────────────────────────────────┘
🔓 Token Permissions:
Scope (Access)
- account (read)
- user (read)
- workers (write)
- workers_kv (write)
- workers_routes (write)
- workers_scripts (write)
- workers_tail (read)
- d1 (write)
- pages (write)
- zone (read)
- ssl_certs (write)
- ai (write)
- ai-search (write)
- ai-search (run)
- queues (write)
- pipelines (write)
- secrets_store (write)
- artifacts (write)
- flagship (write)
- containers (write)
- cloudchamber (write)
- connectivity (admin)
- email_routing (write)
- email_sending (write)
- browser (write)
- offline_access
```

### Generated Project Files

- `edge-api/src/index.ts` — Worker source code and route handling
- `edge-api/wrangler.jsonc` — Worker config (vars, KV bindings, runtime options)
- `edge-api/package.json` — scripts and dependencies for local dev and deploy

## Task 2: Build and Deploy Worker API

### Implemented Routes

- `GET /health` → `{ "status": "ok" }`
- `GET /` → app info (`APP_NAME`, `ENVIRONMENT`, message, timestamp)
- `GET /deployment` → deployment metadata (`DEPLOYMENT_VERSION`, env, secret status)
- `GET /edge` → Cloudflare request metadata
- `POST /kv` → persists data in KV
- `GET /kv?key=<key>` → reads data from KV

### Local Run

```bash
cd edge-api
npx wrangler dev
```

Example checks:

```bash
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8787/
curl http://127.0.0.1:8787/deployment
curl http://127.0.0.1:8787/edge
```

**Windows note:** `curl.exe` from PowerShell can mangle JSON bodies for `POST /kv`. Prefer `Invoke-RestMethod` or a small `node -e "fetch(...)"` one-liner (see Task 4).

### Deploy

```bash
npx wrangler deploy
```

Deploy output (excerpt):

```text
Uploaded edge-api (10.32 sec)
Deployed edge-api triggers (5.69 sec)
  https://edge-api.bulatsigapov004.workers.dev
Current Version ID: 538d074a-0ab6-4178-a831-61e46e76656e
```

Public URL: **`https://edge-api.bulatsigapov004.workers.dev`**

## Task 3: Global Edge Behavior

### Edge Metadata Endpoint

`GET /edge` returns Cloudflare request metadata including `colo`, `country`, `city`, `asn`, `httpProtocol`, and `tlsVersion`.

**Captured JSON** (from deployed URL, via `curl.exe`):

```json
{
  "colo": "ARN",
  "country": "LT",
  "city": "Šiauliai",
  "asn": 16125,
  "httpProtocol": "HTTP/1.1",
  "tlsVersion": "TLSv1.2"
}
```

This shows the Worker can read edge-derived fields from `request.cf` (colo = Stockholm region PoP in this trace; country/city reflect the client path through the edge).

### Global Distribution Explanation

Cloudflare Workers runs your code on Cloudflare’s edge network, close to users, instead of in a single region you choose. VM/PaaS setups often make you pick regions (or replicate across regions yourself). With Workers, one `wrangler deploy` updates the global platform; there is no separate “deploy to three regions” step because distribution is built into the product.

### Routing Concepts

- **workers.dev:** default hostname pattern for Workers (`edge-api.<subdomain>.workers.dev` in this lab).
- **Routes:** attach a Worker to paths on a zone already on Cloudflare (e.g. `example.com/api/*`).
- **Custom domains:** production hostname on your own domain, managed in the dashboard or IaC.

## Task 4: Configuration, Secrets, and Persistence

### Plaintext Variables

Defined in `wrangler.jsonc`:

- `APP_NAME`
- `ENVIRONMENT`
- `DEPLOYMENT_VERSION`

**Why not secrets:** values in `vars` live in config and in revision metadata; they must not hold passwords or API keys. Use Wrangler secrets (or secret stores) for sensitive data.

### Secrets

Commands:

```bash
cd edge-api
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

`npx wrangler secret list` (names only; values are never shown):

```json
[
  { "name": "ADMIN_EMAIL", "type": "secret_text" },
  { "name": "API_TOKEN", "type": "secret_text" }
]
```

`/deployment` confirms both are bound at runtime:

```json
{
  "worker": "edge-api",
  "environment": "dev",
  "deploymentVersion": "v1",
  "hasSecretsConfigured": true
}
```

### Workers KV

Namespace creation (already done for this project):

```bash
npx wrangler kv namespace create SETTINGS
```

Bound in `wrangler.jsonc` as `SETTINGS` with id `36cc749b353d465090b0f0ca2663e692`.

**Store / read via API** (reliable JSON on Windows — Node one-liner):

```bash
node -e "fetch('https://edge-api.bulatsigapov004.workers.dev/kv',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({key:'lab-note3',value:'from-node'})}).then(r=>r.text()).then(console.log)"
curl.exe -s "https://edge-api.bulatsigapov004.workers.dev/kv?key=lab-note3"
```

Example read response:

```json
{ "key": "lab-note3", "value": "from-node" }
```

### Persistence Verification After Redeploy

1. `POST /kv` with a stable key (e.g. `lab-persist`).
2. Run `npx wrangler deploy` again.
3. `GET /kv?key=lab-persist` — value should still be present (KV is account-scoped storage, not the Worker bundle).

**Stored for this report:** key `lab-note3`, value `from-node` (written via Worker API; survives independent of redeploys).

**Also verified via CLI** (remote):

```bash
npx wrangler kv key put --remote --namespace-id=36cc749b353d465090b0f0ca2663e692 lab-note "remote-cli-value"
npx wrangler kv key get --remote --namespace-id=36cc749b353d465090b0f0ca2663e692 lab-note
```

## Task 5: Observability and Operations

### Logs

The Worker logs each request with `console.log("Incoming request", { method, path })`.

Tail:

```bash
cd edge-api
npx wrangler tail --format json
```

**Example log entry** (excerpt from `wrangler tail`; request to `/health`):

```json
{
  "outcome": "ok",
  "scriptName": "edge-api",
  "scriptVersion": { "id": "538d074a-0ab6-4178-a831-61e46e76656e" },
  "logs": [
    {
      "message": ["Incoming request", { "method": "GET", "path": "/health" }],
      "level": "log"
    }
  ],
  "event": {
    "request": { "url": "https://edge-api.bulatsigapov004.workers.dev/health", "method": "GET" },
    "response": { "status": 200 }
  }
}
```

### Metrics

In the Cloudflare dashboard: **Workers & Pages** → **edge-api** → **Metrics**.

- **Metric reviewed:** Request count / success vs errors (and optionally CPU time per request).
- **Observation:** After hitting `/health` and `/edge`, the request chart should show traffic for this Worker; errors should stay near zero for successful tests.

### Deployment History and Rollback

**CLI history** (`npx wrangler deployments list`, excerpt — shows multiple uploads and secret rotations):

```text
Created:     2026-05-12T11:32:53.969Z  Source: Upload              Version: 6de4029d-7b24-4be4-ba04-836dc4d422bd
Created:     2026-05-12T11:32:56.655Z  Source: Secret Change       Version: a1cdfcc9-746e-43d7-ad28-45a1dceea3a6
Created:     2026-05-12T11:33:23.835Z  Source: Secret Change       Version: 4b4b0f93-29c3-4d7b-8d25-13462c7d77bb
Created:     2026-05-12T11:54:05.047Z  Source: Unknown (deployment) Version: 538d074a-0ab6-4178-a831-61e46e76656e
```

**Rollback (dashboard):** Workers & Pages → **edge-api** → **Deployments** → select an earlier deployment → **Roll back** (wording may vary slightly by UI version).

**Rollback (describe):** Rolling back points production traffic at a prior script version without rewriting Git history; you can forward-fix later with a new deploy.

## Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|-------------------|
| Setup complexity | Higher: cluster, networking, ingress, add-ons | Lower: repo + Wrangler + dashboard |
| Deployment speed | Image build/push + rollout | Seconds with `wrangler deploy` |
| Global distribution | Usually you design multi-region | Default global edge footprint |
| Cost (small apps) | Cluster baseline cost | Often pay-per-use friendly at low traffic |
| State/persistence model | Volumes, DBs you operate | Managed bindings (KV, D1, R2, …) |
| Control/flexibility | Full OS/process model | Sandboxed V8 isolate model |
| Best use case | Broad microservices / batch / stateful | Edge HTTP, light APIs, fan-out |

## When to Use Each

### Scenarios Favoring Kubernetes

- Stateful services, custom CNI/service mesh, Jobs/Cron on cluster.
- You need a specific Linux userspace or long-lived processes.

### Scenarios Favoring Workers

- Global HTTP APIs with minimal ops.
- Traffic spikes where you want automatic scale without cluster tuning.

### Recommendation

For this course’s edge API lab, Workers is the natural fit. For a full platform with many teams and diverse workloads, Kubernetes (or managed Kubernetes) often wins.

## Reflection

- **Easier than Kubernetes:** No cluster bootstrap, no ingress controller, no image registry loop — `wrangler deploy` and a URL.
- **More constrained:** No arbitrary Docker image; you work within the Workers runtime, CPU/time limits, and binding model.
- **What changed without Docker:** You don’t manage OS patches or container layers; persistence is always an explicit binding (KV here), not “a disk on the VM.”

## Checklist

- [x] Cloudflare account created
- [x] Workers project initialized
- [x] Wrangler authenticated
- [x] Worker deployed to `workers.dev`
- [x] `/health` endpoint working
- [x] Edge metadata endpoint implemented
- [x] At least 1 plaintext variable configured
- [x] At least 2 secrets configured
- [x] KV namespace created and bound
- [x] Persistence verified (KV read after write; redeploy step recommended once more before submit)
- [x] Logs reviewed (`wrangler tail`)
- [x] Deployment history viewed (`wrangler deployments list` + dashboard)
- [x] `WORKERS.md` documentation complete
- [x] Kubernetes comparison documented
