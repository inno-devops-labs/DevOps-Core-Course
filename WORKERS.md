# Lab 17 - Cloudflare Workers Edge Deployment

## 1. Cloudflare Setup

Project path:

- `workers/edge-api`

Initialization and auth commands:

```bash
cd workers/edge-api
npm install
npx wrangler login
npx wrangler whoami
```

`wrangler.jsonc` role:

- Worker name and entrypoint (`src/index.ts`)
- `workers.dev` enablement
- plain `vars`
- KV bindings (`kv_namespaces`)

## 2. Worker API Implementation

Implemented routes:

- `GET /` - app metadata, environment, available routes
- `GET /health` - health status
- `GET /edge` - edge request metadata (`colo`, `country`, `city`, `asn`, `httpProtocol`, `tlsVersion`, etc.)
- `GET /counter` - persisted counter in Workers KV (`SETTINGS` namespace)
- `GET /config` - confirms vars/secrets configured (without leaking secret values)

Local run:

```bash
cd workers/edge-api
npx wrangler dev
```

Deploy:

```bash
npx wrangler deploy
```

## 3. Global Edge Behavior

Edge metadata endpoint:

```bash
curl https://<worker-name>.<subdomain>.workers.dev/edge
```

What proves edge execution:

- `request.cf` metadata is injected by Cloudflare edge (colo/country/asn/etc.).
- No region selection step is required; traffic is automatically served from Cloudflare global PoPs.

Routing concepts:

- `workers.dev`: instant public Worker URL
- Routes: bind Worker to traffic on an existing Cloudflare zone
- Custom Domains: Worker acts as origin for custom domain/subdomain

## 4. Vars, Secrets, KV

Plaintext vars (`wrangler.jsonc`):

- `APP_NAME`
- `COURSE_NAME`
- `APP_ENV`

Why not for secrets:

- committed in repo config and visible to collaborators.

Secrets (CLI):

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

KV namespace:

```bash
npx wrangler kv namespace create SETTINGS
```

Paste returned namespace `id` into `wrangler.jsonc`:

```json
"kv_namespaces": [
  {
    "binding": "SETTINGS",
    "id": "<REAL_KV_NAMESPACE_ID>"
  }
]
```

Persistence verification:

```bash
curl https://<worker-url>/counter
curl https://<worker-url>/counter
npx wrangler deploy
curl https://<worker-url>/counter
```

Expected: value continues increasing after redeploy.

## 5. Observability and Operations

Worker log statement is present in code:

```ts
console.log("request", { path, method, colo, country, protocol });
```

Tail logs:

```bash
npx wrangler tail
```

Deployments and rollback:

```bash
npx wrangler deployments list
npx wrangler rollback
```

## 6. Deployment Summary (Fill with your real values)

- Worker URL: `https://edge-api-devops-course.mpasgat.workers.dev`
- Routes verified:
  - `/`
  - `/health`
  - `/edge`
  - `/counter`
  - `/config`
- Runtime: Cloudflare Workers (TypeScript)
- State: Workers KV (`SETTINGS`)

Real deployment output:

```text
Deployed edge-api-devops-course triggers
  https://edge-api-devops-course.mpasgat.workers.dev
Current Version ID: 86d03280-0841-4747-9fc3-6f584571badf
```

## 7. Evidence Checklist (Fill during run)

Add screenshots/outputs for:

1. `npx wrangler whoami`
2. successful `npx wrangler deploy` output with public URL
3. `/edge` JSON response (showing colo/country/etc.)
4. secret creation commands success
5. KV namespace creation output
6. `/counter` persistence across redeploy
7. `npx wrangler tail` log sample
8. `npx wrangler deployments list`
9. rollback command/result (or clear explanation if rollback not executed)

Real evidence captured:

```text
npx wrangler whoami
Logged in as asgatk5@gmail.com (OAuth)
```

```text
curl https://edge-api-devops-course.mpasgat.workers.dev/health
{
  "status": "ok",
  "app": "edge-api",
  "env": "prod",
  "timestamp": "2026-05-13T20:45:26.513Z"
}
```

```text
curl https://edge-api-devops-course.mpasgat.workers.dev/edge
{
  "timestamp": "...",
  "edge": {
    "colo": "AMS",
    "country": "NL",
    "city": "Amsterdam",
    "asn": 212706,
    "region": "North Holland",
    "continent": "EU",
    "httpProtocol": "HTTP/2",
    "tlsVersion": "TLSv1.3"
  }
}
```

```text
curl https://edge-api-devops-course.mpasgat.workers.dev/counter
{
  "visits": 1,
  "kvKey": "visits",
  "persisted": true,
  "timestamp": "..."
}
```

```text
npx wrangler tail
GET .../ - Ok
(log) request { path: '/', method: 'GET', colo: 'AMS', country: 'NL', protocol: 'HTTP/2' }
GET .../edge - Ok
(log) request { path: '/edge', method: 'GET', colo: 'AMS', country: 'NL', protocol: 'HTTP/2' }
GET .../counter - Ok
(log) request { path: '/counter', method: 'GET', colo: 'AMS', country: 'NL', protocol: 'HTTP/2' }
```

```text
npx wrangler rollback
SUCCESS Worker Version c8585aaf-8474-4371-a9b2-95996bc182f1 has been deployed to 100% of traffic.
```

```text
npx wrangler deploy
Current Version ID: 86d03280-0841-4747-9fc3-6f584571badf
```

## 8. Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| Setup complexity | Higher: cluster, manifests, networking, lifecycle | Lower: single project + wrangler config |
| Deployment speed | Usually slower (image build + rollout) | Very fast edge deploy |
| Global distribution | You choose/operate regions | Automatic global edge execution |
| Cost (small apps) | Higher baseline overhead | Often cheaper for low/medium traffic |
| State/persistence model | PVC, DBs, StatefulSets | KV/D1/R2/Durable Objects bindings |
| Control/flexibility | Full control of runtime and infra | Less infra control, runtime constraints |
| Best use case | Complex services, long-running workloads | APIs, edge logic, lightweight globally distributed workloads |

## 9. When to Use Each

Use Kubernetes when:

- you need custom runtimes, sidecars, jobs, advanced networking, or stateful clusters.

Use Workers when:

- you need fast global API deployment, low-ops edge execution, and simple serverless scaling.

Recommendation:

- choose Workers for edge APIs and lightweight request processing.
- choose Kubernetes for multi-service platforms with deeper infrastructure control.

## 10. Reflection

Easier than Kubernetes:

- no cluster setup for app runtime, fast deployment, built-in global URL.

More constrained:

- runtime and platform limits, binding-based persistence model.

What changed because Workers is not a Docker host:

- no container image deployment path; application is Workers-native code with bindings.
