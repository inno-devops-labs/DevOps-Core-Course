# Lab 17 Workers Report

## Deployment Summary

- Project: `edge-api`
- Runtime: Cloudflare Workers
- Language: TypeScript
- Worker URL: `https://edge-api.ppepegaa.workers.dev`
- Main routes: `/`, `/health`, `/edge`, `/counter`
- Configuration used:
  - Plaintext vars: `APP_NAME`, `ENVIRONMENT`
  - Secrets: `API_TOKEN`, `ADMIN_EMAIL`
  - KV binding: `COUNTER_KV`

## Evidence

- Cloudflare dashboard screenshots:
  - `edge-api/docs/screenshots/lab17-workers-pages-dashboard.jpg`
  - `edge-api/docs/screenshots/lab17-edge-api-overview-metrics.jpg`
- `wrangler whoami` output:
  - email: `ppepegaa@yandex.ru`
  - account id: `4c8887387612d005efb4e9c4c48ca6cb`
- Deploy output (`npm run deploy`):
  - bundle upload success: `Uploaded edge-api`
  - deploy success: `Deployed edge-api triggers`
  - public URL: `https://edge-api.ppepegaa.workers.dev`
  - current version id: `5123d6ec-c17c-4cd5-9284-36e0a15983bd`
- Example `/edge` JSON response:

```json
{
  "colo": "AMS",
  "country": "NL",
  "city": "Almere Stad",
  "asn": 209847,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3",
  "timestamp": "2026-05-02T10:25:44.927Z"
}
```

- Observability evidence:
  - `wrangler tail` session created successfully (`Connected to edge-api, waiting for logs...`)
  - local runtime log sample from `wrangler dev`:
    - `request { method: 'GET', path: '/health', colo: 'AMS' }`
    - `request { method: 'GET', path: '/edge', colo: 'AMS' }`
  - metrics screenshot: `edge-api/docs/screenshots/lab17-edge-api-overview-metrics.jpg`

## Operations Evidence (Executed)

- Authentication:
  - `wrangler login` -> `Successfully logged in.`
  - `wrangler whoami` -> authenticated account confirmed
- KV created:
  - `COUNTER_KV id = ddf1891f7a4a4bd0af1df04da4cd53c3`
  - `COUNTER_KV preview_id = f77ad273c5924293a2ea6bc015a271e2`
- Secrets created:
  - `API_TOKEN`
  - `ADMIN_EMAIL`
  - verified by `wrangler secret list`
- Deployment history:
  - confirmed by `wrangler deployments list` (includes Upload, Secret Change, and Rollback entries)
- Rollback:
  - executed `wrangler rollback`
  - result: `Worker Version 6d002f5a-b18d-4375-8cdf-662060c4889b has been deployed to 100% of traffic.`
- Remaining blocker:
  - no blocker for `workers.dev` publishing (resolved)

## Public Endpoint Validation (2026-05-02)

- `GET /health` -> `HTTP/2 200`
  - response:
  ```json
  {
    "status": "ok",
    "service": "DevOps Core Edge API",
    "secrets": {
      "apiTokenConfigured": true,
      "adminEmailConfigured": true
    },
    "timestamp": "2026-05-02T10:25:44.445Z"
  }
  ```
- `GET /edge` -> `HTTP/2 200`
  - response:
  ```json
  {
    "colo": "AMS",
    "country": "NL",
    "city": "Almere Stad",
    "asn": 209847,
    "httpProtocol": "HTTP/2",
    "tlsVersion": "TLSv1.3",
    "timestamp": "2026-05-02T10:25:44.927Z"
  }
  ```

## KV Counter Concurrency Contract

- Endpoint: `POST /counter`
- Storage primitive: Cloudflare KV (`COUNTER_KV`)
- Contract: increment is implemented as read-modify-write and is **not atomic**.
- Impact under concurrency: parallel writes can race and some increments can be lost.
- Recommendation for strict monotonic counters: move increment logic to Durable Objects (single-writer coordination) or another atomic primitive.
- Current API behavior: `/counter` GET/POST responses include a `note` field that explicitly communicates this limitation.

## Persistence After Redeploy Verification (2026-05-02)

- Goal: verify that KV-backed counter state survives Worker redeploys.
- Preconditions:
  - `COUNTER_KV` is bound in `wrangler.jsonc`
  - production URL is known (example: `https://edge-api.ppepegaa.workers.dev`)
- Steps:
  1. Reset counter and set known baseline:
     - `curl -X DELETE https://edge-api.ppepegaa.workers.dev/counter`
     - `curl -X POST https://edge-api.ppepegaa.workers.dev/counter`
  2. Capture pre-deploy value:
     - `curl https://edge-api.ppepegaa.workers.dev/counter`
     - expected example: `{ "key": "global:counter", "value": 1, "note": "..." }`
  3. Redeploy Worker code:
     - `cd edge-api && npm run deploy`
  4. Read counter after deploy:
     - `curl https://edge-api.ppepegaa.workers.dev/counter`
  5. Verify persistence condition:
     - post-deploy `value` must be `>=` pre-deploy value and not reset to `0` unless DELETE/reset was executed.
- Fixed evidence example (2026-05-02):
  - redeploy version id: `5123d6ec-c17c-4cd5-9284-36e0a15983bd`
  - pre-deploy (`GET /counter` before redeploy): `{ "key": "global:counter", "value": 1, "note": "..." }`
  - post-deploy (`GET /counter` after redeploy): `{ "key": "global:counter", "value": 1, "note": "..." }`
  - conclusion: counter value persisted across redeploy (no reset to `0`).

## Routing Concepts

- `workers.dev`:
  - Default Cloudflare-hosted subdomain endpoint (`<worker>.<account>.workers.dev`)
  - Fastest path for labs/testing and public verification.
- Routes:
  - Bind Worker to path patterns on an existing zone/domain (for example `example.com/api/*`)
  - Useful when integrating with an existing website and DNS zone.
- Custom Domains:
  - Attach Worker directly to a custom hostname managed in Cloudflare.
  - Better for production API identity and certificate-managed branded endpoints.
- Practical selection:
  - Lab/POC: `workers.dev`
  - Existing site path integration: Routes
  - Dedicated production hostname: Custom Domains

## Short Evidence Artifact Notes (No Secrets)

- `edge-api/docs/screenshots/lab17-workers-pages-dashboard.jpg`:
  - Confirms Worker presence in Cloudflare dashboard UI.
- `edge-api/docs/screenshots/lab17-edge-api-overview-metrics.jpg`:
  - Confirms requests/observability signals in metrics view.
- Curl response captures for `/health`, `/edge`, `/counter`:
  - Keep timestamps/status/route payloads.
  - Do not include secret values, tokens, emails, `.dev.vars`, or CLI secret input logs.

## Kubernetes vs Cloudflare Workers (7 Aspects)

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| Setup complexity | Cluster setup, ingress, manifests, autoscaling config | Fast start via `wrangler`, platform-managed runtime |
| Deployment speed | Slower rollout path (build, push image, apply manifests) | Very fast publish to edge with `wrangler deploy` |
| Global distribution | Usually explicit multi-region architecture and ops overhead | Global edge distribution by default |
| Cost (for small apps) | Often higher baseline cost (nodes/control plane/managed services) | Usually lower entry cost for low-traffic edge APIs |
| State/persistence model | You operate DB/storage and network paths | Use managed bindings (KV/D1/R2) via platform |
| Control/flexibility | Maximum control of runtime/network/policies | Constrained runtime, less low-level control |
| Best use case | Complex platforms, heavy custom infra, full control needs | Lightweight APIs, edge logic, globally distributed request handling |

## When to Use Each

- Scenarios favoring Kubernetes: stateful microservices, strict infra/network control, custom sidecars/operators.
- Scenarios favoring Workers: edge APIs, request enrichment, geo-aware routing, rapid global rollout.
- Recommendation: for this lab-style HTTP API with simple persistence and global reach, Workers is the more pragmatic default.

## Reflection

Workers felt easier than Kubernetes for deployment and distribution because there is no cluster lifecycle management. Main constraints were runtime/binding boundaries and reduced low-level control. The design changed because Workers is not a Docker host: instead of packaging a container, the app relies on Worker bindings (`vars`, `secrets`, `KV`) and edge-native deployment workflow.

## Why Plaintext Vars Are Not Suitable for Secrets

Plaintext vars from `wrangler.jsonc` are configuration values that can be exposed in repository history, local files, CI logs, and team-visible config surfaces. Secrets (`wrangler secret put ...`) are encrypted and managed separately by Cloudflare, reducing accidental disclosure risk. Therefore `API_TOKEN` and `ADMIN_EMAIL` must be stored as secrets, not plaintext vars.

## Operations / Rollback Runbook

1. Pre-check:
   - `npx wrangler whoami`
   - `npm run check`
2. Deploy:
   - `npm run deploy`
3. Validate production:
   - `curl https://<worker-url>/health`
   - `curl https://<worker-url>/edge`
   - `curl https://<worker-url>/counter`
4. Observe runtime logs:
   - `npx wrangler tail`
   - Confirm log events include `method`, `path`, `colo`
5. Inspect deployment history:
   - `npx wrangler deployments list`
6. Rollback if regression detected:
   - `npx wrangler rollback`
   - Re-run validation curls
7. Post-incident:
   - Capture evidence, update this report, and document root cause/fix.
