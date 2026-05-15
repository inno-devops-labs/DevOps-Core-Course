# Lab 17 — Cloudflare Workers Edge Deployment

This document records the implementation and verification steps for Lab 17. The Worker project lives in [`edge-api/`](./), and the lab rubric remains in [`labs/lab17.md`](../labs/lab17.md).

## Deployment Summary

- Worker name: `edge-api`
- Runtime: Cloudflare Workers (TypeScript, ES modules)
- Public URL: `https://edge-api.andreygamer366.workers.dev`
- Account verification: completed separately with `npx wrangler whoami`
- Current deployed app version: `1.0.1`
- Current Cloudflare version ID: `af1bf96c-9fe7-4841-b910-9bfc2963a2cb`
- Main routes:

| Route | Method | Purpose |
|------|--------|---------|
| `/` | `GET` | Service metadata, runtime info, and endpoint inventory |
| `/health` | `GET` | Basic health response with UTC timestamp |
| `/edge` | `GET` | Cloudflare edge metadata from `request.cf` |
| `/counter` | `GET` | Workers KV persistence demo |
| `/admin` | `GET` | Secret-backed route using `x-api-token` |

## Configuration Used

### Plaintext vars in `wrangler.jsonc`

```jsonc
"vars": {
  "APP_NAME": "edge-api",
  "COURSE_NAME": "DevOps Core Course",
  "APP_VERSION": "1.0.1"
}
```

Why plaintext vars are acceptable here:
- They hold app metadata and course configuration, not secrets.
- Cloudflare environment variables are visible configuration, so they are not suitable for passwords or tokens.

### Required secrets

Create these secrets before testing `/admin` or deploying:

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

Local development example:

```dotenv
API_TOKEN="replace-with-local-dev-token"
ADMIN_EMAIL="student@example.com"
```

Do not commit the real `.dev.vars` or `.env` files.

### Workers KV binding

Create the namespace and then replace the placeholder ID in [`wrangler.jsonc`](./wrangler.jsonc):

```bash
npx wrangler kv namespace create SETTINGS
```

The namespace created for this lab is:

```text
SETTINGS => cb5b72b2ab72416a9cf6f6f79841a348
```

Expected binding block:

```jsonc
"kv_namespaces": [
  {
    "binding": "SETTINGS",
    "id": "<real-kv-namespace-id>"
  }
]
```

Note for local development:
- `wrangler dev` uses local KV by default.
- If you want local code to hit the deployed namespace, add `"remote": true` to the KV binding after the namespace exists.

### Observability

Workers Logs is enabled in [`wrangler.jsonc`](./wrangler.jsonc):

```jsonc
"observability": {
  "enabled": true,
  "head_sampling_rate": 1
}
```

## Implementation Notes

The Worker intentionally mirrors the shape of the earlier Python course service while adapting to the Workers runtime:

- [`src/index.ts`](./src/index.ts) returns service metadata from `/`, similar to the existing Flask app.
- `/health` provides a minimal health contract suitable for public checks.
- `/edge` exposes request metadata such as `colo`, `country`, `city`, `asn`, `httpProtocol`, and `tlsVersion`.
- `/counter` persists a `visits` key in Workers KV and includes an explicit note that KV is eventually consistent.
- `/admin` validates `x-api-token` against `API_TOKEN` and returns only a masked form of `ADMIN_EMAIL`.
- A safe `console.log()` statement records path, method, and non-sensitive edge metadata for observability.

## Verification Commands

### Local development

```bash
cd edge-api
npm install
npx wrangler dev
```

In another terminal:

```bash
curl http://127.0.0.1:8787/
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8787/edge
curl http://127.0.0.1:8787/counter
curl -i http://127.0.0.1:8787/admin
curl -i -H "x-api-token: replace-with-local-dev-token" http://127.0.0.1:8787/admin
```

### Deployment

```bash
cd edge-api
npx wrangler deploy
```

After deployment, test the public Worker:

```bash
curl https://<worker-name>.<your-subdomain>.workers.dev/health
curl https://<worker-name>.<your-subdomain>.workers.dev/edge
curl https://<worker-name>.<your-subdomain>.workers.dev/counter
curl -i -H "x-api-token: <real-token>" https://<worker-name>.<your-subdomain>.workers.dev/admin
```

### Deployments and rollback

Create at least two code deployments, then inspect history:

```bash
npx wrangler deployments list
```

Rollback options:

```bash
npx wrangler rollback
npx wrangler rollback <VERSION_ID>
```

Deployment history completed during this lab:

```text
Initial code deployment: 74c3f1f4-7769-403b-ac87-6ab89fc43b12
Second code deployment:  d5aeb9a2-2703-4c9f-97ee-aaeb1ae22d2a
Rollback demo:           deployed 74c3f1f4-7769-403b-ac87-6ab89fc43b12 with message "Lab 17 rollback demo"
Restored latest code:    af1bf96c-9fe7-4841-b910-9bfc2963a2cb
```

## Evidence

### Example `/edge` response

```json
{
  "runtime": "cloudflare-workers",
  "metadata": {
    "colo": "HEL",
    "country": "FI",
    "city": "Vantaa",
    "asn": 13335,
    "httpProtocol": "HTTP/2",
    "tlsVersion": "TLSv1.3"
  },
  "note": "request.cf metadata is only populated by the Workers runtime, so verify this endpoint against the deployed workers.dev URL."
}
```

### Persistence check

```text
Before second code deploy: visits = 1
After second code deploy:  visits = 2
After rollback + restore:  visits = 3
Conclusion: KV data persisted across code deployments and rollback operations because the namespace binding remained attached.
```

### Logs / metrics

Capture either:
- `npx wrangler tail` output showing the route log line, or
- the Worker Observability dashboard showing requests/logs.

```text
Example tail log:
GET https://edge-api.andreygamer366.workers.dev/health - Ok @ 5/15/2026, 6:59:48 AM
  (log) request { path: '/health', method: 'GET', colo: 'HEL', country: 'FI' }
```

### Required screenshots

Do not automate screenshots with Wrangler or headless tooling.

Take these manually and place them in [`screenshots/`](./screenshots/):
- `worker-overview.png` showing the Worker overview and `workers.dev` URL
- `observability.png` showing logs or metrics after exercising the Worker
- `deployments.png` showing at least two deployments or a rollback entry

## Kubernetes vs Cloudflare Workers Comparison

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| Setup complexity | Cluster, ingress, manifests, secrets, and ongoing ops | Much lighter for small APIs; project + deploy + bindings |
| Deployment speed | Usually slower due to image build, push, scheduling, and rollout | Very fast upload and global publish |
| Global distribution | Usually requires multi-region cluster design or provider features | Built into the platform by default |
| Cost for small apps | Can be expensive or operationally heavy | Often cheaper and simpler for low-traffic APIs |
| State / persistence | Flexible but explicit: volumes, DBs, operators, services | Bindings-based; KV, D1, R2, Durable Objects |
| Control / flexibility | Full container/runtime/network control | Less control; code must fit the Workers runtime model |
| Best use case | Long-running services, custom runtimes, complex networking | Edge APIs, lightweight request handling, globally distributed logic |

## When To Use Each

Prefer Kubernetes when:
- You need full container control or a custom runtime.
- You run stateful or long-lived services.
- You need advanced networking, sidecars, or operator-based integrations.

Prefer Workers when:
- You need a lightweight public API at the edge.
- You want fast deployment with minimal platform management.
- Your workload fits request/response execution and binding-based state.

Recommendation:
- For this lab and similar lightweight APIs, Workers is the faster and simpler fit.
- For larger service platforms or container-native systems, Kubernetes remains the more flexible choice.

## Reflection

What felt easier than Kubernetes:
- No container image build, registry push, or cluster scheduling was required.
- Public access through `workers.dev` is much faster to get running.
- Secrets, vars, logs, and KV are integrated into the platform workflow.

What felt more constrained:
- The runtime is not a Docker host, so the app had to be rewritten for the Workers execution model.
- Storage and networking options are platform-specific and more opinionated.
- Some request metadata such as `request.cf` only appears in the real runtime, not every local preview path.

What changed because Workers is not a Docker host:
- The API became a single request handler instead of a traditional process listening on a port.
- State moved from filesystem/container assumptions to a platform binding (`SETTINGS`).
- Operational tasks shifted from cluster resources to Wrangler commands and dashboard views.
