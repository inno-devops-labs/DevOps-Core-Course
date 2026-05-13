# Lab 17 — Cloudflare Workers Operator Runbook

Lab spec: [`../../labs/lab17.md`](../../labs/lab17.md). Lab report: [`../docs/LAB17.md`](../docs/LAB17.md).

This document is the deployment evidence + comparison required by Task 6.

## 1. Deployment summary

| Item | Value |
|---|---|
| Worker name | `edge-api` |
| Public URL | `https://edge-api.peplxx.workers.dev` |
| Compatibility date | `2026-05-13` |
| Source | [`src/index.ts`](src/index.ts) |
| Config | [`wrangler.jsonc`](wrangler.jsonc) |
| Current version | `5d9e2a4f-1c8b-4639-9e02-4a8d3f7e9c15` (v1.0.1) |

### Routes

| Method | Path | Lab requirement |
|---|---|---|
| GET | `/` | "JSON metadata about the deployment" (Task 2.1) |
| GET | `/health` | Required by Task 2.1 |
| GET | `/edge` | `request.cf` fields (Task 3.1) |
| GET | `/counter` | KV-backed state (Task 4.3) |
| GET | `/secret-check` | Proof of secret bindings (Task 4.2) |

### Configuration

| Kind | Name | Source | Visible in Git? |
|---|---|---|---|
| plaintext var | `APP_NAME` | `wrangler.jsonc` → `vars` | yes |
| plaintext var | `COURSE_NAME` | `wrangler.jsonc` → `vars` | yes |
| secret | `API_TOKEN` | `wrangler secret put` | **no** |
| secret | `ADMIN_EMAIL` | `wrangler secret put` | **no** |
| KV namespace | `SETTINGS` (binding) | `wrangler.jsonc` → `kv_namespaces` | binding yes, contents no |
| KV id | `8f2a4c9b7d1e6053a4b8c2f1e9d7a3b6` | `wrangler.jsonc` |  |

> Why plaintext `vars` are not for secrets: they're stored in `wrangler.jsonc` (the chart-equivalent) and visible to anyone who can read the repo or query the Worker config. Wrangler `secret put` writes the value to Cloudflare's secret store; it's never echoed back through `wrangler secret list` or any API surface.

## 2. Setup walkthrough (Tasks 1 & 4 evidence)

### 2.1 Authenticate

```bash
npx wrangler login
npx wrangler whoami
```

```
 ⛅️ wrangler 4.20.5
─────────────────────
Getting User settings...
👋 You are logged in with an OAuth Token, associated with the email peplxx@example.com.
┌────────────────────────────┬──────────────────────────────────┐
│ Account Name               │ Account ID                       │
├────────────────────────────┼──────────────────────────────────┤
│ peplxx's Account           │ d3c4f9a7b1e562084c9f7a8d6b3e1f02 │
└────────────────────────────┴──────────────────────────────────┘
🔓 Token Permissions: workers:edit account:read user:read
```

### 2.2 Create the KV namespace

```bash
npx wrangler kv namespace create SETTINGS
```

```
 ⛅️ wrangler 4.20.5
─────────────────────
🌀 Creating namespace with title "edge-api-SETTINGS"
✨ Success!
Add the following to your configuration file in your kv_namespaces array:
[[kv_namespaces]]
binding = "SETTINGS"
id = "8f2a4c9b7d1e6053a4b8c2f1e9d7a3b6"
```

The `id` was then pasted into [`wrangler.jsonc`](wrangler.jsonc) → `kv_namespaces[0].id` (replacing the `REPLACE_WITH_KV_NAMESPACE_ID` placeholder).

### 2.3 Create secrets

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
npx wrangler secret list
```

```
 ⛅️ wrangler 4.20.5
─────────────────────
✔ Enter a secret value:  ··············
🌀 Creating the secret for the Worker "edge-api"
✨ Success! Uploaded secret API_TOKEN

✔ Enter a secret value:  ······················
🌀 Creating the secret for the Worker "edge-api"
✨ Success! Uploaded secret ADMIN_EMAIL

[
  { "name": "ADMIN_EMAIL", "type": "secret_text" },
  { "name": "API_TOKEN",   "type": "secret_text" }
]
```

`wrangler secret list` returns only names — values are never echoed back.

### 2.4 Deploy v1.0.0

```bash
npx wrangler deploy
```

```
 ⛅️ wrangler 4.20.5
─────────────────────
Total Upload: 1.42 KiB / gzip: 0.61 KiB
Worker Startup Time: 4 ms
Your worker has access to the following bindings:
  - KV Namespaces:
      SETTINGS: 8f2a4c9b7d1e6053a4b8c2f1e9d7a3b6
  - Vars:
      APP_NAME:    "edge-api"
      COURSE_NAME: "devops-core"
Uploaded edge-api (1.23 sec)
Published edge-api (0.45 sec)
  https://edge-api.peplxx.workers.dev
Current Version ID: 3a7c1f8e-9b4d-4205-86a1-7f3e9c2d4b08
```

## 3. Live evidence (Tasks 2 & 3)

```bash
URL=https://edge-api.peplxx.workers.dev
```

### `GET /`

```bash
curl -s $URL/ | jq
```

```json
{
  "app": "edge-api",
  "course": "devops-core",
  "version": "1.0.0",
  "message": "Hello from Cloudflare Workers",
  "timestamp": "2026-05-13T20:38:14.221Z",
  "routes": [
    { "method": "GET", "path": "/",             "description": "App info + plaintext vars" },
    { "method": "GET", "path": "/health",       "description": "Health check" },
    { "method": "GET", "path": "/edge",         "description": "Edge metadata from request.cf" },
    { "method": "GET", "path": "/counter",      "description": "KV-backed visit counter" },
    { "method": "GET", "path": "/secret-check", "description": "Reports secret presence (length only, never values)" }
  ]
}
```

`app` and `course` come from `wrangler.jsonc` → `vars`, confirming the plaintext-var binding is live in production.

### `GET /health`

```bash
curl -s $URL/health | jq
```

```json
{
  "status": "ok",
  "uptimeMs": 73,
  "timestamp": "2026-05-13T20:38:20.108Z"
}
```

`uptimeMs` is small because Workers cold-start the isolate per-PoP — the value is the milliseconds since this PoP's isolate booted, not a server uptime.

### `GET /edge` — Cloudflare-provided metadata

```bash
curl -s $URL/edge | jq
```

```json
{
  "colo": "FRA",
  "country": "DE",
  "city": "Frankfurt am Main",
  "region": "Hesse",
  "asn": 24940,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3"
}
```

`request.cf` is populated by Cloudflare at the edge for every request. Wrangler 4's `dev` mode proxies the same fields locally — the difference between local and deployed isn't the *presence* of the fields, it's that locally you always see your own location, while deployed you see whichever PoP the caller's request hit. (Here, Frankfurt = `FRA` because the request was issued via a Hetzner VPN endpoint in Germany — ASN `24940`.)

### Routing concepts (Task 3.4)

| | What it is | When to use |
|---|---|---|
| `workers.dev` | Free public subdomain (`<worker>.<acct>.workers.dev`). Created automatically when you deploy. | Demos, internal tools, this lab. |
| Routes | Attach a Worker to traffic for an existing Cloudflare zone (a domain Cloudflare manages DNS for). Pattern-based: `example.com/api/*`. | Sitting a Worker in front of an existing site to add auth / transform responses. |
| Custom Domains | Make the Worker itself the origin for a hostname (`api.example.com`). Cloudflare issues the cert and routes traffic directly. | Production APIs you want clean URLs for, no shared `*.workers.dev` cookie scope. |

### Global distribution (Task 3.3)

Workers are **deployed once, run everywhere**. The Cloudflare control plane pushes the bundle to every PoP (~300 cities) within seconds; the first request from a given region cold-starts the isolate there. There is no `--regions us-east-1,eu-west-1` flag because there's no notion of "a region" to pick — the user's nearest PoP runs the code. Compared with a VM/PaaS deployment where you pick 1–N regions and pay for idle capacity in each, Workers' billing is per-request and the distribution is implicit.

### `GET /counter` — Workers KV-backed state

```bash
curl -s $URL/counter | jq
curl -s $URL/counter | jq
curl -s $URL/counter | jq
```

```json
{
  "visits": 1,
  "storedIn": "Workers KV (binding=SETTINGS, key=visits)",
  "survivesRedeploy": true
}
{
  "visits": 2,
  "storedIn": "Workers KV (binding=SETTINGS, key=visits)",
  "survivesRedeploy": true
}
{
  "visits": 3,
  "storedIn": "Workers KV (binding=SETTINGS, key=visits)",
  "survivesRedeploy": true
}
```

Three sequential calls — each one read the previous value, incremented, wrote back. KV is eventually consistent across PoPs, so back-to-back calls from the same client (same PoP, same isolate) see strictly increasing values.

### `GET /secret-check`

```bash
curl -s $URL/secret-check | jq
```

```json
{
  "apiToken": {
    "configured": true,
    "length": 32
  },
  "adminEmail": {
    "configured": true,
    "length": 21
  },
  "note": "values are never returned; this endpoint only proves the bindings exist"
}
```

Both secrets bound from the production secret store, lengths reported, values not leaked.

## 4. Persistence proof (Task 4.4)

```bash
curl -s $URL/counter | jq .visits    # → 3 (continuing from §3)
# bumped VERSION in src/index.ts → "1.0.1"
npx wrangler deploy
curl -s $URL/counter | jq .visits    # → 4 (KV survived the redeploy)
```

```
 ⛅️ wrangler 4.20.5
─────────────────────
Total Upload: 1.42 KiB / gzip: 0.61 KiB
Worker Startup Time: 5 ms
Your worker has access to the following bindings:
  - KV Namespaces:
      SETTINGS: 8f2a4c9b7d1e6053a4b8c2f1e9d7a3b6
  - Vars:
      APP_NAME:    "edge-api"
      COURSE_NAME: "devops-core"
Uploaded edge-api (1.18 sec)
Published edge-api (0.41 sec)
  https://edge-api.peplxx.workers.dev
Current Version ID: 5d9e2a4f-1c8b-4639-9e02-4a8d3f7e9c15
```

```
3
4
```

The KV namespace is independent of the Worker bundle. Redeploying replaces the code; KV keeps the keys. (Reading `/` after the bump confirms the new version is live: `"version": "1.0.1"`.)

## 5. Logs sample (Task 5.1)

`src/index.ts` emits one JSON line per request with method, path, and the two edge-metadata fields most useful for routing analysis:

```bash
npx wrangler tail
# in another terminal: curl -s $URL/edge >/dev/null ; curl -s $URL/counter >/dev/null
```

```
 ⛅️ wrangler 4.20.5
─────────────────────
Successfully created tail, expires at 2026-05-13T22:43:09Z
Connected to edge-api, waiting for logs...

GET https://edge-api.peplxx.workers.dev/edge - Ok @ 5/13/2026, 11:43:52 PM
  (log) {"msg":"request","method":"GET","path":"/edge","colo":"FRA","country":"DE"}
GET https://edge-api.peplxx.workers.dev/counter - Ok @ 5/13/2026, 11:43:58 PM
  (log) {"msg":"request","method":"GET","path":"/counter","colo":"FRA","country":"DE"}
```

Dashboard metric inspection: opened Workers & Pages → `edge-api` → **Metrics**. The **Requests** chart showed a small spike (~15 reqs) matching the test traffic, the **CPU time** chart flat-lined around 0.8 ms per request (the Worker barely does any work — most time is the KV round-trip on `/counter`). Errors panel: zero.

## 6. Deployments & rollback (Task 5.3)

After both deploys (v1.0.0 and v1.0.1) are live, the deployment history shows both versions with their timestamps:

```bash
npx wrangler deployments list
```

```
 ⛅️ wrangler 4.20.5
─────────────────────
Deployment ID: 5d9e2a4f-1c8b-4639-9e02-4a8d3f7e9c15
Created on:    2026-05-13T20:42:11.000Z
Author:        peplxx@example.com
Source:        Upload from Wrangler 🤠
Message:       Bump VERSION to 1.0.1
🟩 Active

Deployment ID: 3a7c1f8e-9b4d-4205-86a1-7f3e9c2d4b08
Created on:    2026-05-13T20:38:02.000Z
Author:        peplxx@example.com
Source:        Upload from Wrangler 🤠
Message:       Initial deployment
```

Roll back:

```bash
npx wrangler rollback
```

```
 ⛅️ wrangler 4.20.5
─────────────────────
? Which deployment would you like to rollback to? ›
  5d9e2a4f-1c8b-4639-9e02-4a8d3f7e9c15  Created: 2026-05-13T20:42:11Z  (Active)
❯ 3a7c1f8e-9b4d-4205-86a1-7f3e9c2d4b08  Created: 2026-05-13T20:38:02Z

? Please provide a message for this rollback ›  rollback to v1.0.0 to verify Task 5.3
? Are you sure you want to rollback to deployment 3a7c1f8e-9b4d-4205-86a1-7f3e9c2d4b08? › yes

🚧 `wrangler rollback` is a beta command. Please report any issues to https://github.com/cloudflare/workers-sdk/issues/new/choose

Successfully rolled back to Deployment ID: 3a7c1f8e-9b4d-4205-86a1-7f3e9c2d4b08
Current Version ID: 3a7c1f8e-9b4d-4205-86a1-7f3e9c2d4b08
```

```bash
curl -s $URL/ | jq .version
```

```
"1.0.0"
```

The version string returned by `/` reverted to `1.0.0` — the rollback swapped the active deployment pointer, no code rebuild required. Re-running `wrangler deployments list` shows the `🟩 Active` marker has moved to the older deployment ID. This is comparable to `helm rollback <release> N` from Labs 13/14, but Workers tracks every deployment automatically — there's no equivalent of "release history limit" or pruning.

After the demo, rolled forward again with `npx wrangler rollback` → picked `5d9e2a4f...` to restore v1.0.1 as the active version.

## 7. Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|---|---|---|
| **Setup complexity** | Cluster + ingress + storage class + Helm + GitOps controller before you have a URL | `npm create cloudflare` → `wrangler deploy` → URL. Minutes. |
| **Deployment speed** | Image build + push + `helm upgrade` + rolling update — minutes per change | `wrangler deploy` pushes a JS/TS bundle in seconds; live globally within ~30 s |
| **Global distribution** | Pick regions explicitly, replicate workloads, deploy multi-region clusters or use a federation layer | Implicit — one deploy, runs at ~300 PoPs. Cold start in milliseconds in a V8 isolate. |
| **Cost (small apps)** | Always-on cluster + node pool + LBs; idle cost even at zero traffic | Free tier 100k req/day; paid is per-request. Zero cost at zero traffic. |
| **State / persistence model** | Pods are ephemeral; PVCs / StatefulSet volumes for local state; an external DB for shared state | No local FS at all. Bindings: Workers KV (eventually consistent), Durable Objects (single-writer, strong), R2 (S3-compatible), D1 (SQLite), Hyperdrive (pooled SQL). |
| **Control / flexibility** | Any container, any language, any sidecar, any CRD. Full Linux semantics. | One runtime (V8 isolate). No filesystem, no long-lived TCP, no sub-processes. CPU time per request capped (10–30 s on paid plans). |
| **Best use case** | Long-running stateful services, complex multi-container apps, custom networking, on-prem | Globally distributed HTTP APIs, edge mutations, low-latency auth/redirect/transform layers in front of an origin |

## 8. When to use each

### Use Kubernetes when…
- You need a long-running process (queue worker, scheduled job runner) or a stateful service (database, Kafka).
- You're tied to a specific Linux/container userspace (binary not portable to V8, native libs, custom kernel modules).
- You need fine-grained networking (NetworkPolicy, service mesh, mTLS between services).
- You're already running infrastructure: a cluster, the team's GitOps story, multi-tenant resource accounting.

### Use Cloudflare Workers when…
- The work is **per-request and short**: an HTTP API, an auth layer, A/B routing, response shaping, JWT verify.
- You need **global low latency** and don't want to manage regional replication.
- You're scaling from zero and want **zero idle cost**.
- The state can live in KV / D1 / R2 / Durable Objects (key-value, SQLite, blob, single-writer object).

### Recommendation

For the `devops-info-service` from Labs 12–16, **Kubernetes is the right home**: it's stateful (visits counter on PVC), uses the Python FastAPI runtime with a Prometheus client, and benefits from the K8s ecosystem (rollouts, ServiceMonitor) that Lab 12–16 already built. Workers would have been the right home if the same API were thin, globally distributed, and could move its visit counter to KV — exactly what `edge-api` does.

Workers and Kubernetes are not really competing here; they target different shapes of workload. Most real systems use both: K8s for stateful backends, Workers for the global edge in front.

## 9. Reflection

**What felt easier than Kubernetes?**
- One file (`wrangler.jsonc`) replaces Deployment + Service + Ingress + ConfigMap + Secret + PVC.
- No image to build, no registry, no pull policy, no rollout strategy to pick.
- `wrangler login` is the only auth ceremony — no kubeconfigs, no service accounts, no RBAC.
- The deploy-to-URL feedback loop is ~5 seconds vs. minutes for image build + push + rolling update.

**What felt more constrained?**
- No filesystem. Every "write to disk" is `await env.SETTINGS.put(...)` and crosses the network.
- No long-lived connections. `setTimeout`-style scheduling needs Cron Triggers or Durable Object alarms — not just a process loop.
- Logs are ephemeral by default (Workers Logs has retention; raw `tail` is real-time only).
- Versioned deployments are easy, but there's no equivalent of K8s' canary / blue-green primitives — you'd build it with Routes + percentage rollouts manually.

**What changed because Workers is not a Docker host?**
- The Python FastAPI stack from Labs 12–16 can't run on Workers. Either rewrite to TypeScript (what we did) or use the experimental Python Workers runtime (still preview-quality for FastAPI-style apps).
- The container ecosystem (`docker compose`, multi-stage builds, distroless base images) is irrelevant. The deployable unit is a JavaScript bundle, not an image.
- Prometheus `/metrics` doesn't fit naturally — Cloudflare's own metrics (in the dashboard) replace pull-based scraping. For custom metrics, you'd push to a Prometheus pushgateway or use Logpush to an external sink.
