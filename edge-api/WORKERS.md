# Lab 17 Report — Cloudflare Workers Edge Deployment

## 1. Deployment Summary

This lab implements a Cloudflare Workers-native HTTP API in TypeScript. It is not a Docker deployment: the Worker runs in Cloudflare's edge runtime and uses platform bindings for configuration, secrets, and KV persistence.

Project path:

```text
edge-api/
├── src/index.ts
├── wrangler.jsonc
├── package.json
├── tsconfig.json
└── WORKERS.md
```

Worker name:

```text
edge-api-devops
```

Public URL after deployment:

```text
https://edge-api-devops.sofia-devops-labs.workers.dev
```

Main routes:

| Route | Method | Purpose |
|---|---|---|
| `/` | `GET` | Service metadata and route list |
| `/health` | `GET` | Health check |
| `/edge` | `GET` | Cloudflare request metadata: colo, country, city, ASN, protocol, TLS |
| `/config` | `GET` | Plain variables and secret presence, without exposing secret values |
| `/counter` | `GET` | KV-backed persistent visit counter |
| `/settings` | `GET` | Read persisted KV value |
| `/settings` | `PUT` | Store persisted KV value |

## 2. Cloudflare Setup

Required local tools:

```bash
node --version
npm --version
```

Verified local versions:

```text
Node.js v23.11.0
npm 10.9.2
```

Install dependencies:

```bash
cd edge-api
npm install
```

Authenticate Wrangler:

```bash
npx wrangler login
npx wrangler whoami
```

Wrangler OAuth authorization in Cloudflare:

![Wrangler OAuth authorization](<screenshots/Screenshot 2026-05-14 at 12.15.51.png>)

`wrangler.jsonc` is the Worker configuration file. It defines the Worker name, entry point, compatibility date, `workers.dev` routing, plaintext variables, observability, and KV bindings.

## 3. Configuration, Secrets, and KV

Plaintext variables configured in `wrangler.jsonc`:

```json
"vars": {
  "APP_NAME": "edge-api-devops",
  "COURSE_NAME": "devops-core-course",
  "APP_VERSION": "v1"
}
```

Plaintext vars are suitable for non-sensitive values because they are stored in project configuration and can be committed. They must not be used for passwords, API tokens, private keys, or personal data.

Secrets are created through Wrangler and are not committed:

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

KV namespace creation:

```bash
npx wrangler kv namespace create SETTINGS
```

Wrangler returns an id. Put that id into `wrangler.jsonc`:

```json
"kv_namespaces": [
  {
    "binding": "SETTINGS",
    "id": "3afc8e96d9344d1aa68c23f1f5b7e23b"
  }
]
```

For local development only, create `.dev.vars` from the example file:

```bash
cp .dev.vars.example .dev.vars
```

`.dev.vars` is ignored by Git.

## 4. Local Development

Run the Worker locally:

```bash
npm run dev
```

Test routes:

```bash
curl http://127.0.0.1:8787/
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8787/edge
curl http://127.0.0.1:8787/config
curl http://127.0.0.1:8787/counter
curl -X PUT http://127.0.0.1:8787/settings \
  -H 'content-type: application/json' \
  -d '{"value":"deployed for lab17"}'
curl http://127.0.0.1:8787/settings
```

Expected local `/health` response:

```json
{
  "status": "ok",
  "app": "edge-api-devops",
  "version": "v1",
  "timestamp": "2026-05-13T11:02:00.684Z"
}
```

Verified local `/edge` response:

```json
{
  "colo": "ARN",
  "country": "FI",
  "city": "Helsinki",
  "asn": 56971,
  "httpProtocol": "HTTP/1.1",
  "tlsVersion": "TLSv1.3",
  "clientIpPresent": true
}
```

Verified local `/config` response:

```json
{
  "app": "edge-api-devops",
  "course": "devops-core-course",
  "version": "v1",
  "adminEmailConfigured": true,
  "apiTokenConfigured": true,
  "note": "Secret values are read from env bindings but are not returned."
}
```

Verified local KV counter response:

```json
{
  "key": "visits",
  "visits": 1,
  "persisted": true,
  "storage": "Cloudflare Workers KV",
  "timestamp": "2026-05-13T11:02:00.698Z"
}
```

Verified local `/settings` write/read:

```json
{
  "key": "deployment-note",
  "value": "deployed for lab17",
  "stored": true
}
```

```json
{
  "key": "deployment-note",
  "value": "deployed for lab17",
  "exists": true
}
```

## 5. Deployment

Deploy to `workers.dev`:

```bash
npm run deploy
```

After deployment, test the public URL:

```bash
export WORKER_URL="https://edge-api-devops.sofia-devops-labs.workers.dev"

curl "$WORKER_URL/"
curl "$WORKER_URL/health"
curl "$WORKER_URL/edge"
curl "$WORKER_URL/config"
curl "$WORKER_URL/counter"
```

Verified public `/health` response:

```json
{
  "status": "ok",
  "app": "edge-api-devops",
  "version": "v1",
  "timestamp": "2026-05-14T09:12:34.423Z"
}
```

Verified public `/edge` response:

```json
{
  "colo": "ARN",
  "country": "FI",
  "city": "Helsinki",
  "asn": 56971,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3",
  "clientIpPresent": true
}
```

Verified public `/counter` response:

```json
{
  "key": "visits",
  "visits": 1,
  "persisted": true,
  "storage": "Cloudflare Workers KV",
  "timestamp": "2026-05-14T09:12:47.636Z"
}
```

The `colo`, `country`, and protocol values prove the request was handled with Cloudflare edge metadata.

Public endpoint verification:

![Public endpoint verification](<screenshots/Screenshot 2026-05-14 at 12.13.38.png>)

Cloudflare Workers dashboard with the deployed Worker:

![Cloudflare Workers dashboard](<screenshots/Screenshot 2026-05-14 at 12.25.53.png>)

Cloudflare account overview showing Workers and Pages activity:

![Cloudflare account overview](<screenshots/Screenshot 2026-05-14 at 12.26.55.png>)

Worker overview with public URL, metrics, and KV binding:

![Worker overview and binding](<screenshots/Screenshot 2026-05-14 at 12.27.11.png>)

## 6. Persistence Verification

The `/counter` endpoint stores a `visits` key in Workers KV:

```bash
curl "$WORKER_URL/counter"
curl "$WORKER_URL/counter"
```

Expected behavior:

```json
{
  "key": "visits",
  "visits": 2,
  "persisted": true,
  "storage": "Cloudflare Workers KV"
}
```

Redeploy:

```bash
npm run deploy
```

Verify the value continues increasing after redeploy:

```bash
curl "$WORKER_URL/counter"
```

This proves state is stored outside the Worker code package in Cloudflare Workers KV.

The `/settings` endpoint stores and reads another KV value:

```bash
curl -X PUT "$WORKER_URL/settings" \
  -H 'content-type: application/json' \
  -d '{"value":"persisted after redeploy"}'

curl "$WORKER_URL/settings"
```

## 7. Observability and Operations

The Worker logs each request:

```ts
console.log("request", {
  method: request.method,
  path: url.pathname,
  colo: request.cf?.colo,
  country: request.cf?.country,
});
```

Tail logs:

```bash
npm run tail
```

Example log shape:

```text
request { method: "GET", path: "/edge", colo: "AMS", country: "NL" }
```

Verified local log entries:

```text
request { method: 'GET', path: '/health', colo: 'ARN', country: 'FI' }
request { method: 'GET', path: '/config', colo: 'ARN', country: 'FI' }
request { method: 'GET', path: '/edge', colo: 'ARN', country: 'FI' }
request { method: 'GET', path: '/counter', colo: 'ARN', country: 'FI' }
request { method: 'PUT', path: '/settings', colo: 'ARN', country: 'FI' }
request { method: 'GET', path: '/settings', colo: 'ARN', country: 'FI' }
```

Metrics are visible in the Cloudflare dashboard:

```text
Workers & Pages -> edge-api-devops -> Metrics
```

Metrics to review:

- request count
- errors
- invocation duration
- status codes

Metrics and deployments in the Cloudflare dashboard:

![Cloudflare metrics and deployments](<screenshots/Screenshot 2026-05-14 at 12.45.49.png>)

Deployment history:

```bash
npm run deployments
```

Verified deployment history:

```text
Created:     2026-05-14T09:01:35.668Z
Source:      Upload
Version(s):  d8d405ea-ba7f-4b39-ad4f-c77a1242bc28

Created:     2026-05-14T09:01:38.776Z
Source:      Secret Change
Version(s):  dd1626bc-f46a-4132-92d8-8bb56404b4c3

Created:     2026-05-14T09:01:59.781Z
Source:      Secret Change
Version(s):  73a1460c-c404-476b-b793-55766843bf13

Created:     2026-05-14T09:05:09.344Z
Source:      Unknown (deployment)
Version(s):  72bd061f-5ff0-4d68-a99c-c830337d27e2
```

Wrangler deployment history:

![Wrangler deployment history](<screenshots/Screenshot 2026-05-14 at 12.44.48.png>)

Deploy at least two versions by changing `APP_VERSION` in `wrangler.jsonc`, for example from `v1` to `v2`, then running:

```bash
npm run deploy
npm run deployments
```

Rollback options:

```bash
npx wrangler rollback
```

or use:

```text
Cloudflare Dashboard -> Workers & Pages -> edge-api-devops -> Deployments -> Rollback
```

## 8. Routing Concepts

`workers.dev` is the default public development/deployment domain for Workers. It gives a public URL without owning a separate domain.

Routes attach a Worker to paths on an existing Cloudflare-managed zone, such as `example.com/api/*`.

Custom Domains expose the Worker directly on a domain or subdomain, such as `api.example.com`, without using the `workers.dev` hostname.

This lab uses `workers.dev` because it is enough to prove public edge deployment without DNS zone setup.

## 9. Global Edge Behavior

Cloudflare Workers run on Cloudflare's global network. Requests are routed to a nearby Cloudflare location, and the Worker receives metadata through `request.cf`, such as `colo`, `country`, `city`, `asn`, `httpProtocol`, and `tlsVersion`.

There is no manual `deploy to 3 regions` step. Deployment is uploaded to Cloudflare, and Cloudflare handles global distribution. This is different from VMs or many PaaS platforms, where a team often chooses regions, provisions capacity, and configures traffic routing.

## 10. Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|---|---|---|
| Setup complexity | Higher: cluster, nodes, manifests, ingress, observability | Lower: project, Wrangler, deploy |
| Deployment speed | Depends on image builds, registry pushes, scheduling | Fast code upload to edge runtime |
| Global distribution | Manual multi-region clusters or external traffic routing | Built into Cloudflare's global network |
| Cost for small apps | Can be overkill because cluster baseline costs exist | Usually cheaper for small HTTP APIs |
| State/persistence model | Volumes, databases, StatefulSets, external services | KV, Durable Objects, D1, R2, external APIs |
| Control/flexibility | High: any containerized runtime and long-running workloads | More constrained runtime, no Docker host |
| Best use case | Complex services, internal platforms, long-running workloads | Lightweight HTTP APIs, edge logic, redirects, auth, global low-latency reads |

## 11. When to Use Each

Use Kubernetes when the workload needs containers, long-running processes, custom networking, sidecars, persistent volumes, operators, or many services with strict internal platform control.

Use Cloudflare Workers when the workload is request-driven, lightweight, globally distributed, and can use Workers platform services for state and configuration.

My recommendation: use Workers for small public APIs, edge metadata/routing, webhook handlers, auth gates, and global read-heavy endpoints. Use Kubernetes for the existing Flask app and other container workloads that need full Linux/runtime control.

## 12. Reflection

Workers felt easier than Kubernetes for public exposure, HTTPS, global routing, and deployment speed. There is no ingress controller, Service, Deployment, or image registry step.

Workers felt more constrained because it is not a Docker host. The app must be written for the Workers runtime, and persistence must use platform bindings such as KV rather than a mounted volume.

The biggest design change is that operational concerns move from Kubernetes objects to Cloudflare configuration: `wrangler.jsonc`, vars, secrets, KV bindings, logs, metrics, and deployment history.

## 13. Evidence Checklist

Screenshots added:

- Cloudflare OAuth authorization
- Cloudflare Workers dashboard showing `edge-api-devops`
- Public `/health`, `/edge`, and `/counter` responses
- `/edge` response with `colo` and `country`
- KV binding in the Worker overview
- Metrics dashboard
- Deployment history
