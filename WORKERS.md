# Lab 17 - Cloudflare Workers Edge Deployment

Run date: May 7, 2026

This branch implements the updated Lab 17 assignment as a Cloudflare Workers TypeScript API in `labs/lab17/edge-api`.
The previous Fly.io artifact was removed because the current upstream lab explicitly requires Workers and notes that this is not a Docker-hosted deployment.

## Deployment Summary

Worker project:

- name: `devops-edge-api`
- source: `labs/lab17/edge-api/src/index.ts`
- config: `labs/lab17/edge-api/wrangler.jsonc`
- runtime: Cloudflare Workers
- public route type: `workers.dev`

Expected public URL after deployment:

```text
https://devops-edge-api.<cloudflare-workers-subdomain>.workers.dev
```

Routes:

| Route | Purpose |
| --- | --- |
| `/` | API summary, route list, app metadata |
| `/health` | JSON health check |
| `/edge` | Cloudflare request metadata such as `colo`, `country`, `city`, `asn`, `httpProtocol`, `tlsVersion` |
| `/config` | Plaintext vars from `wrangler.jsonc` |
| `/secrets` | Presence check for secret bindings without exposing values |
| `/counter` | KV-backed persistent visit counter |

## Cloudflare Setup

Commands used for setup and verification:

```powershell
cd .\labs\lab17\edge-api
npm install
npx wrangler login
npx wrangler whoami
```

`workers.dev` gives a Worker a public Cloudflare-managed URL without configuring a custom domain.
`wrangler.jsonc` declares the Worker entrypoint, compatibility date, plaintext vars, observability, and KV binding names.

## Local Development

Run locally:

```powershell
cd .\labs\lab17\edge-api
npm run dev
```

Test local routes:

```powershell
Invoke-RestMethod http://127.0.0.1:8787/
Invoke-RestMethod http://127.0.0.1:8787/health
Invoke-RestMethod http://127.0.0.1:8787/edge
Invoke-RestMethod http://127.0.0.1:8787/config
Invoke-RestMethod http://127.0.0.1:8787/secrets
Invoke-RestMethod http://127.0.0.1:8787/counter
```

Validation:

```text
npm run typecheck
npm run deploy:dry-run
```

## Configuration, Secrets, and KV

Plaintext vars in `wrangler.jsonc`:

```json
"vars": {
  "APP_NAME": "devops-edge-api",
  "COURSE_NAME": "devops-core",
  "DEPLOYMENT_ENV": "lab17"
}
```

Plaintext vars are committed to Git and are only suitable for non-sensitive values.
Secret values must be created through Wrangler and must not be committed:

```powershell
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

KV namespace creation:

```powershell
npx wrangler kv namespace create SETTINGS
npx wrangler kv namespace create SETTINGS --preview
```

Paste the returned IDs into `wrangler.jsonc`:

```json
"kv_namespaces": [
  {
    "binding": "SETTINGS",
    "id": "<production-id>",
    "preview_id": "<preview-id>"
  }
]
```

Persistence verification:

```powershell
Invoke-RestMethod https://devops-edge-api.<subdomain>.workers.dev/counter
npx wrangler deploy
Invoke-RestMethod https://devops-edge-api.<subdomain>.workers.dev/counter
```

The second response should continue incrementing the same `visits` key after redeploy because the value is stored in Workers KV, not in process memory.

## Edge Metadata Evidence

The `/edge` endpoint returns request metadata supplied by Cloudflare at the edge:

```json
{
  "colo": "WAW",
  "country": "PL",
  "city": "Warsaw",
  "asn": 13335,
  "httpProtocol": "HTTP/3",
  "tlsVersion": "TLSv1.3",
  "timezone": "Europe/Warsaw"
}
```

The exact values depend on the client network path and Cloudflare point of presence.

Workers are globally distributed by Cloudflare automatically. Unlike VM or PaaS deployments, there is no manual "deploy to three regions" step: Cloudflare routes requests to nearby edge locations and runs the Worker there.

Routing concepts:

- `workers.dev`: Cloudflare-managed public URL for a Worker
- Routes: attach a Worker to URL patterns on an existing Cloudflare zone
- Custom Domains: assign a domain or subdomain directly to a Worker

## Observability and Operations

The Worker logs one structured entry per request:

```ts
console.log("request", {
  path: url.pathname,
  method: request.method,
  colo: request.cf?.colo ?? "local",
});
```

Tail logs:

```powershell
npm run tail
```

Inspect deployment history and rollback:

```powershell
npx wrangler deployments list
npx wrangler rollback
```

Dashboard evidence to capture in a live account:

- Worker request count
- Worker error count
- deployment history with at least two versions
- log entry from a request to `/edge` or `/counter`

## Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
| --- | --- | --- |
| Setup complexity | Cluster, manifests, networking, controllers | Account, Worker config, bindings |
| Deployment speed | Depends on image build, pull, rollout | Usually seconds with Wrangler |
| Global distribution | Manual multi-region design | Automatic Cloudflare edge distribution |
| Cost for small apps | Cluster overhead exists even at low traffic | Low overhead, usage-based |
| State model | Volumes, databases, operators, services | KV, Durable Objects, D1, R2 bindings |
| Control | High control over runtime and networking | More constrained runtime |
| Best use case | Long-running services and complex platforms | Lightweight APIs, routing, edge logic |

Use Kubernetes when the workload needs custom runtimes, long-running containers, complex networking, or stateful platform components.
Use Workers when the workload is an HTTP API or edge function that benefits from fast global distribution and low operational overhead.

Workers changed the Lab 2 mental model: there is no Docker image to deploy here. The source code targets the Workers runtime directly, while config, secrets, and state are injected through Cloudflare bindings.
