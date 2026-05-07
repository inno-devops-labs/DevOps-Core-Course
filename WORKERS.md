# Lab 17 - Cloudflare Workers Edge Deployment

## Deployment Summary

The lab implementation is in `edge-api`. It is a TypeScript Cloudflare Worker configured with Wrangler, plaintext variables, two expected secrets, and a Workers KV namespace binding.

Worker name: `devops-edge-api`

Public URL:

```text
https://devops-edge-api.utevaugu36.workers.dev
```

Main routes:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | Returns app metadata, runtime metadata, request details, and available routes. |
| `GET` | `/health` | Returns health status for uptime checks. |
| `GET` | `/edge` | Returns Cloudflare edge metadata from `request.cf`, including `colo`, `country`, `city`, `asn`, `httpProtocol`, and `tlsVersion`. |
| `GET` | `/counter` | Reads and increments the persisted `visits` value in Workers KV. |
| `POST` | `/counter/reset` | Resets the persisted counter to `0`. |
| `GET` | `/config` | Shows plaintext variables and confirms secret presence without returning secret values. |

Configuration used:

| Setting | Value |
| --- | --- |
| Runtime | Cloudflare Workers |
| Source | `edge-api/src/index.ts` |
| Config | `edge-api/wrangler.jsonc` |
| Compatibility date | `2026-05-07` |
| Plaintext vars | `APP_NAME`, `COURSE_NAME`, `APP_ENV` |
| Secrets | `API_TOKEN`, `ADMIN_EMAIL` |
| KV binding | `SETTINGS` -> `a1f2a09c6f004158ba21aa81e33efbb3` |
| Preview KV namespace | `27a79597c5eb41e9a723ef5b8009b807` |
| Observability | Enabled in Wrangler config |

## Local Verification

Install dependencies:

```bash
cd edge-api
bun install
```

Run type checking and tests:

```bash
bun run check
```

Run locally:

```bash
bun run dev
```

Example local route checks:

```bash
curl http://127.0.0.1:8787/
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8787/edge
curl http://127.0.0.1:8787/counter
curl http://127.0.0.1:8787/config
```

## Cloudflare Setup Commands

Authenticate:

```bash
cd edge-api
bunx wrangler login
bunx wrangler whoami
```

Create KV namespaces:

```bash
bunx wrangler kv namespace create SETTINGS
bunx wrangler kv namespace create SETTINGS --preview
```

The created namespace IDs are already stored in `edge-api/wrangler.jsonc`.

Create secrets:

```bash
bunx wrangler secret put API_TOKEN
bunx wrangler secret put ADMIN_EMAIL
```

Deploy:

```bash
bunx wrangler deploy
```

Verify production:

```bash
curl https://devops-edge-api.utevaugu36.workers.dev/
curl https://devops-edge-api.utevaugu36.workers.dev/health
curl https://devops-edge-api.utevaugu36.workers.dev/edge
curl https://devops-edge-api.utevaugu36.workers.dev/counter
curl https://devops-edge-api.utevaugu36.workers.dev/config
```

## Evidence

The local network had intermittent direct Cloudflare API access, so deployment was completed with the Cloudflare REST API through an HTTP proxy. The repository still keeps the standard Wrangler project and `wrangler.jsonc`; `bunx wrangler deploy --dry-run` validates the Worker bundle and bindings locally.

| Evidence | Status |
| --- | --- |
| Cloudflare dashboard screenshot | Capture from dashboard if image evidence is required |
| Public Worker URL | `https://devops-edge-api.utevaugu36.workers.dev` |
| `/edge` JSON response | Captured below |
| Tail log session | Tail API session created, WebSocket blocked by local network |
| Metrics view | Observability enabled, inspect request count and errors in dashboard |
| Deployment history | Captured below |

Wrangler dry run:

```text
$ bunx wrangler deploy --dry-run
Total Upload: 4.60 KiB / gzip: 1.44 KiB
env.SETTINGS (a1f2a09c6f004158ba21aa81e33efbb3)  KV Namespace
env.APP_NAME ("devops-edge-api")                  Environment Variable
env.COURSE_NAME ("DevOps Core Course")            Environment Variable
env.APP_ENV ("production")                        Environment Variable
--dry-run: exiting now.
```

Health check:

```json
{
  "status": "ok",
  "app": "devops-edge-api",
  "environment": "production",
  "timestamp": "2026-05-07T14:04:19.460Z"
}
```

Edge metadata:

```json
{
  "edge": {
    "colo": "FRA",
    "country": "DE",
    "city": "Frankfurt am Main",
    "asn": 58212,
    "httpProtocol": "HTTP/2",
    "tlsVersion": "TLSv1.3"
  },
  "request": {
    "clientIp": "2a0d:5940:43:1c::",
    "userAgent": "curl/8.7.1"
  }
}
```

Config and secret binding verification:

```json
{
  "appName": "devops-edge-api",
  "courseName": "DevOps Core Course",
  "environment": "production",
  "secrets": {
    "apiTokenConfigured": true,
    "adminEmailConfigured": true
  }
}
```

KV persistence verification:

```json
{
  "key": "visits",
  "visits": 1,
  "persisted": true
}
```

```json
{
  "key": "visits",
  "visits": 2,
  "persisted": true
}
```

Workers.dev subdomain verification:

```json
{
  "enabled": true,
  "previews_enabled": true
}
```

Deployment history:

```text
15eec860-38ba-4f3f-8132-c14cad936636  secret  2026-05-07T14:03:46.939597Z
08ac597f-ff7c-4c28-9ccb-b1539d825682  secret  2026-05-07T14:03:29.608012Z
db18dc42-decb-4761-9c8e-8812f3b2cf73  upload  2026-05-07T14:03:09.033485Z
```

Tail session created:

```text
wss://tail.developers.workers.dev/d641948c08ac44c0b314d8bce91cee3e
```

## Global Edge Behavior

Cloudflare Workers does not require manually choosing three deployment regions. The Worker script is deployed to Cloudflare's global network, and requests execute close to the user at the nearest available Cloudflare location. The `/edge` endpoint reads `request.cf` metadata so the response can show the Cloudflare colo and request geography used for that execution.

This differs from VM or PaaS platforms where the operator selects regions, scales machines per region, and manages capacity placement. With Workers, global distribution is part of the runtime model.

Routing concepts:

| Concept | Meaning |
| --- | --- |
| `workers.dev` | A Cloudflare-provided public hostname for quick Worker deployment. |
| Route | A rule that attaches a Worker to traffic for an existing Cloudflare zone. |
| Custom Domain | A domain or subdomain configured so the Worker serves requests directly. |

This lab uses `workers.dev` because it is enough for a public edge API and does not require owning or configuring a separate DNS zone.

## Configuration, Secrets, and Persistence

Plaintext variables in `wrangler.jsonc` are suitable for non-sensitive configuration such as app name, course name, and environment. They are committed to source control, so they must not contain passwords, tokens, private URLs, or personal credentials.

Secrets are configured with `wrangler secret put`. The Worker reads `API_TOKEN` and `ADMIN_EMAIL` through the `env` object, but `/config` only returns boolean presence checks. This proves the bindings are available without exposing secret values.

Workers KV is bound as `SETTINGS`. The `/counter` route stores the `visits` value and increments it on every request. After a redeploy, calling `/counter` again should continue from the previously stored value because KV state is outside the Worker code bundle.

## Observability and Operations

The Worker emits a structured enough log line for each request:

```text
request <method> <path> <colo>
```

View live logs:

```bash
bunx wrangler tail
```

View deployments:

```bash
bunx wrangler deployments list
```

Deploy a second version by changing a non-sensitive variable or source response and running:

```bash
bunx wrangler deploy
```

Rollback:

```bash
bunx wrangler rollback
```

In the Cloudflare dashboard, inspect Workers metrics such as request count, errors, and invocation duration. For this lab, request count and error rate are the most useful because the API is small and route health is easy to validate with `curl`.

## Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
| --- | --- | --- |
| Setup complexity | Requires cluster, nodes, networking, ingress, RBAC, manifests, and operational conventions. | Requires a Cloudflare account, Wrangler, a Worker config, and optional bindings. |
| Deployment speed | Slower because images must build, push, roll out, and pass Kubernetes readiness checks. | Fast because Wrangler uploads a Worker bundle directly to the edge platform. |
| Global distribution | Manual region and cluster planning, or a managed multi-region platform on top. | Automatic global execution on Cloudflare's network. |
| Cost for small apps | Often higher due to baseline cluster or node costs. | Usually lower for small HTTP APIs because there is no always-on VM requirement. |
| State and persistence model | Supports many storage models, including PVCs, databases, operators, and stateful workloads. | Uses platform bindings such as KV, Durable Objects, D1, R2, and external services. |
| Control and flexibility | High control over runtime, containers, networking, scheduling, and sidecars. | More constrained runtime with no arbitrary Docker container, but less infrastructure to manage. |
| Best use case | Complex services, containerized workloads, private networking, stateful systems, and teams needing platform control. | Lightweight HTTP APIs, request routing, middleware, global low-latency endpoints, and edge integrations. |

## When to Use Each

Use Kubernetes when the system needs container-level control, private service meshes, long-running processes, custom networking, complex stateful workloads, or a shared platform for many teams.

Use Cloudflare Workers when the workload is request-driven, latency-sensitive, globally distributed, and can fit the Workers runtime and binding model.

My recommendation for this lab service is Cloudflare Workers. The app is a small HTTP API with simple configuration, request metadata, health checks, and a lightweight persisted counter. Workers handles the global edge concerns directly, while Kubernetes would add operational weight that the service does not need.

## Reflection

Workers felt easier than Kubernetes for public deployment, TLS, global routing, and a simple release workflow. There is no cluster bootstrap, ingress controller, image registry, or regional machine placement to manage.

Workers felt more constrained because the application must fit the Workers runtime. It cannot run the existing Docker image directly, and persistence must use Cloudflare bindings or external managed services instead of a local filesystem or PVC.
