# Lab 17 — Cloudflare Workers Edge Deployment

## 1. Deployment Summary

This lab implements a serverless HTTP API using Cloudflare Workers and Wrangler.

Worker name:

```text
edge-api
```

Public Workers URL:

```text
https://edge-api.a-fayzullin.workers.dev
```

The Worker was built with:

- Cloudflare Workers
- Wrangler CLI
- TypeScript
- Workers KV
- Environment variables
- Secrets

Main routes:

| Route | Purpose |
|---|---|
| `/` | General service information |
| `/health` | Health check endpoint |
| `/edge` | Cloudflare edge metadata |
| `/config` | Configuration and secret status |
| `/counter` | KV-backed persistent counter |
| `/kv` | Reads persisted KV value |

---

## 2. Cloudflare Setup

The Cloudflare account was authenticated through Wrangler.

Command:

```bash
npx wrangler login
npx wrangler whoami
```

Verification output:

```text
You are logged in with an OAuth Token, associated with the email a.fayzullin@innopolis.university.

Account Name:
A.fayzullin@innopolis.university's Account

Account ID:
a58cb45edf30b195d624c8fcf036d081
```

This confirmed that Wrangler was connected to the Cloudflare account.

---

## 3. Worker Project

The Worker project was created using Cloudflare C3:

```bash
npm create cloudflare@latest -- edge-api
```

Selected options:

```text
Hello World example
Worker only
TypeScript
Git: Yes
Deploy now: No
```

Important project files:

| File | Purpose |
|---|---|
| `src/index.ts` | Worker source code |
| `wrangler.jsonc` | Worker configuration |
| `package.json` | npm scripts and dependencies |

---

## 4. Worker API Implementation

The Worker implements several HTTP endpoints.

Example TypeScript environment interface:

```ts
export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}
```

The Worker uses:

- request routing through `url.pathname`
- `Response.json()` for JSON responses
- `request.cf` for Cloudflare edge metadata
- `env` bindings for configuration, secrets, and KV storage
- `console.log()` for observability

---

## 5. Local Development

The Worker was run locally with Wrangler:

```bash
npx wrangler dev
```

Wrangler started the local development server:

```text
Ready on http://localhost:8787
```

Local endpoint checks:

```bash
curl http://localhost:8787/
curl http://localhost:8787/health
curl http://localhost:8787/edge
curl http://localhost:8787/config
```

Example local `/health` response:

```json
{
  "status": "ok",
  "service": "edge-api"
}
```

---

## 6. Production Deployment

The Worker was deployed using:

```bash
npx wrangler deploy
```

Deployment output:

```text
Uploaded edge-api
Deployed edge-api triggers
https://edge-api.a-fayzullin.workers.dev
```

Public URL:

```text
https://edge-api.a-fayzullin.workers.dev
```

---

## 7. Public API Verification

The deployed Worker was tested through the public `workers.dev` URL.

### Root endpoint

Command:

```bash
curl https://edge-api.a-fayzullin.workers.dev/
```

Output:

```json
{
  "app": "edge-api",
  "course": "devops-core",
  "message": "Hello from Cloudflare Workers",
  "routes": ["/", "/health", "/edge", "/config", "/counter", "/kv"]
}
```

### Health endpoint

Command:

```bash
curl https://edge-api.a-fayzullin.workers.dev/health
```

Output:

```json
{
  "status": "ok",
  "service": "edge-api"
}
```

---

## 8. Edge Metadata Endpoint

The `/edge` endpoint returns Cloudflare request metadata from `request.cf`.

Command:

```bash
curl https://edge-api.a-fayzullin.workers.dev/edge
```

Output:

```json
{
  "colo": "AMS",
  "country": "NL",
  "city": "Halfweg",
  "asn": 55286,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3",
  "timezone": "Europe/Amsterdam"
}
```

This proves that the Worker is running on Cloudflare's edge network and receiving edge-specific metadata.

The observed Cloudflare colo was:

```text
AMS
```

Country:

```text
NL
```

---

## 9. Global Edge Behavior

Cloudflare Workers do not require manually selecting deployment regions.

Instead of deploying to specific VM or Kubernetes regions, Workers are distributed through Cloudflare's global edge network. Requests are routed to a nearby Cloudflare data center automatically.

Comparison:

| Traditional VM/PaaS | Cloudflare Workers |
|---|---|
| Choose region manually | Runs on global edge |
| Need multi-region setup | Global distribution built in |
| Load balancers required | Cloudflare routing built in |
| More infrastructure control | Less infrastructure to manage |

There is no separate "deploy to 3 regions" step because Workers are globally distributed by the platform.

---

## 10. Routing Concepts

### workers.dev

`workers.dev` provides a default public URL for quick deployments.

Used in this lab:

```text
https://edge-api.a-fayzullin.workers.dev
```

### Routes

Routes attach a Worker to traffic for an existing Cloudflare-managed domain or zone.

Example use case:

```text
example.com/api/*
```

### Custom Domains

Custom Domains allow a Worker to be served directly from a custom domain or subdomain.

Example:

```text
api.example.com
```

This lab used `workers.dev`, which satisfies the required public deployment.

---

## 11. Environment Variables

Plaintext environment variables were configured in `wrangler.jsonc`.

Configuration:

```jsonc
"vars": {
  "APP_NAME": "edge-api",
  "COURSE_NAME": "devops-core"
}
```

These values are safe to commit because they are not sensitive.

They were used in Worker responses:

```json
{
  "app": "edge-api",
  "course": "devops-core"
}
```

Plaintext variables are not suitable for passwords, API keys, or tokens because they are stored in the project configuration file.

---

## 12. Secrets

Two secrets were created using Wrangler:

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

The values were not committed to Git.

The `/config` endpoint confirms that secrets are configured without exposing their values.

Command:

```bash
curl https://edge-api.a-fayzullin.workers.dev/config
```

Output:

```json
{
  "appName": "edge-api",
  "courseName": "devops-core",
  "adminEmailConfigured": true,
  "apiTokenConfigured": true,
  "note": "Secrets are configured through Wrangler."
}
```

This confirms that both secrets are available through the `env` object.

---

## 13. Workers KV Persistence

A KV namespace was created:

```bash
npx wrangler kv namespace create SETTINGS
```

KV namespace binding in `wrangler.jsonc`:

```jsonc
"kv_namespaces": [
  {
    "binding": "SETTINGS",
    "id": "df7715bf380b4f51828e7652f763870c",
    "remote": true
  }
]
```

The Worker uses KV to persist a counter.

Endpoint:

```text
/counter
```

Test:

```bash
curl https://edge-api.a-fayzullin.workers.dev/counter
curl https://edge-api.a-fayzullin.workers.dev/counter
```

Output:

```json
{"visits":1,"persisted":true,"storage":"Workers KV"}
{"visits":2,"persisted":true,"storage":"Workers KV"}
```

---

## 14. Persistence After Redeploy

After redeploying the Worker:

```bash
npx wrangler deploy
```

The persisted value was still available.

Command:

```bash
curl https://edge-api.a-fayzullin.workers.dev/kv
```

Output:

```json
{
  "key": "visits",
  "value": "2"
}
```

Then the counter was incremented again:

```bash
curl https://edge-api.a-fayzullin.workers.dev/counter
```

Output:

```json
{
  "visits": 3,
  "persisted": true,
  "storage": "Workers KV"
}
```

This proves that Workers KV state survives redeployments.

---

## 15. Observability

### Console Logging

The Worker includes a `console.log()` statement:

```ts
console.log(
  "request",
  url.pathname,
  "colo",
  request.cf?.colo,
  "country",
  request.cf?.country
);
```

`wrangler tail` was tested:

```bash
npx wrangler tail
```

However, the command failed due to a connectivity issue:

```text
A fetch request failed, likely due to a connectivity issue.
ERROR fetch failed
```

This was likely related to network path or Cloudflare connectivity restrictions. The Worker itself was successfully deployed and reachable publicly.

### Metrics

Metrics were reviewed in the Cloudflare dashboard.

Observed areas:

- request count
- deployments
- Worker overview
- public route status

Screenshots are stored in:

```text
labs/lab17/screenshots/
```

---

## 16. Deployment History

Deployment history was viewed using:

```bash
npx wrangler deployments list
```

Output included several deployments and secret changes:

```text
Created:     2026-05-15T08:15:13.259Z
Author:      a.fayzullin@innopolis.university
Source:      Upload
Message:     Automatic deployment on upload.

Created:     2026-05-15T08:24:13.418Z
Author:      a.fayzullin@innopolis.university
Source:      Unknown (deployment)

Created:     2026-05-15T08:26:22.013Z
Author:      a.fayzullin@innopolis.university
Source:      Unknown (deployment)
```

Current deployment version observed:

```text
8aa50722-17e3-4079-8570-3c7242b846dd
```

Rollback can be performed with:

```bash
npx wrangler rollback
```

A rollback would move traffic back to a previous deployed version.

---

## 17. Screenshots

Screenshots are stored in:

```text
labs/lab17/screenshots/
```
---

## 18. Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|---|---|---|
| Setup complexity | Higher, requires cluster, manifests, controllers | Lower, mostly CLI and platform configuration |
| Deployment speed | Depends on image build, registry, cluster rollout | Very fast upload and deploy |
| Global distribution | Requires multi-region clusters or external routing | Built into Cloudflare edge network |
| Cost for small apps | Can be high due to cluster/node overhead | Usually cheaper for small APIs |
| State/persistence model | PVCs, databases, StatefulSets, external storage | KV, D1, R2, Durable Objects |
| Control/flexibility | Very high, any container/runtime | More constrained runtime |
| Best use case | Complex containerized systems and long-running workloads | Lightweight APIs, edge routing, global request handling |

---

## 19. When to Use Each

### Kubernetes is better when:

- the application requires containers
- long-running background processes are needed
- advanced networking is required
- multiple services need orchestration
- stateful workloads need PVCs or StatefulSets
- custom runtime dependencies are required

### Cloudflare Workers is better when:

- the app is a lightweight HTTP API
- low latency and global availability are important
- there is no need to manage servers
- edge metadata or request routing is useful
- small-scale cost efficiency matters
- deployments should be simple and fast

---

## 20. Reflection

Cloudflare Workers felt easier than Kubernetes for:

- public deployment
- HTTPS access
- global distribution
- simple HTTP routing
- configuration through bindings

Cloudflare Workers felt more constrained because:

- it is not a Docker host
- there is no full Linux container environment
- runtime capabilities are limited compared with Kubernetes
- persistence uses platform services such as KV instead of mounted volumes

The biggest difference from Kubernetes is that Workers are not deployed as containers. Instead of building and pushing Docker images, the application is written for the Workers runtime and deployed directly with Wrangler.

---

## 21. Summary

This lab successfully implemented a Cloudflare Workers edge API.

Completed:

- Cloudflare account setup
- Wrangler authentication
- TypeScript Worker project
- public `workers.dev` deployment
- `/health` endpoint
- `/edge` metadata endpoint
- plaintext vars
- two Wrangler secrets
- Workers KV namespace
- persistent KV counter
- persistence after redeploy
- deployment history
- Kubernetes vs Workers comparison

The final Worker is publicly available at:

```text
https://edge-api.a-fayzullin.workers.dev
```
