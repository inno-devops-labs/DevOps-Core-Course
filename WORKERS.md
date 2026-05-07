# Lab 17 - Cloudflare Workers Edge Deployment

Run date: May 7, 2026

## Summary

I updated Lab 17 to match the current upstream assignment. The old Fly.io configuration was removed because the lab now requires a Cloudflare Workers-native API, not a Docker-hosted service.

The solution is implemented as a TypeScript Worker in `labs/lab17/edge-api`.

## Implemented Files

| File | Purpose |
| --- | --- |
| `labs/lab17/edge-api/src/index.ts` | Worker API routes and request handling |
| `labs/lab17/edge-api/wrangler.jsonc` | Worker config, vars, observability, KV binding |
| `labs/lab17/edge-api/package.json` | Wrangler and TypeScript scripts |
| `labs/lab17/edge-api/tsconfig.json` | Strict TypeScript config |
| `labs/lab17/edge-api/worker-configuration.d.ts` | Typed Worker bindings |
| `labs/lab17/edge-api/package-lock.json` | Locked Node dependency versions |
| `.gitignore` | Ignores `node_modules`, `.wrangler`, `.dev.vars`, `dist` |

Removed obsolete file:

- `app_python/fly.toml`

## Worker API

Worker name:

```text
devops-edge-api
```

Expected public URL after deployment:

```text
https://devops-edge-api.<cloudflare-workers-subdomain>.workers.dev
```

Routes:

| Route | Purpose |
| --- | --- |
| `/` | API summary, route list, app metadata |
| `/health` | Health check |
| `/edge` | Cloudflare edge metadata: `colo`, `country`, `city`, `asn`, `httpProtocol`, `tlsVersion`, `timezone` |
| `/config` | Plaintext Worker vars from `wrangler.jsonc` |
| `/secrets` | Secret binding presence checks without exposing values |
| `/counter` | KV-backed persistent visit counter |

## Configuration

Plaintext variables are stored in `wrangler.jsonc`:

```json
"vars": {
  "APP_NAME": "devops-edge-api",
  "COURSE_NAME": "devops-core",
  "DEPLOYMENT_ENV": "lab17"
}
```

These are safe to commit because they are not secret. Sensitive values are read from Worker secret bindings:

- `API_TOKEN`
- `ADMIN_EMAIL`

Secrets are intentionally not committed. They must be created with:

```powershell
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

KV binding:

```json
"kv_namespaces": [
  {
    "binding": "SETTINGS",
    "id": "replace-with-production-kv-namespace-id",
    "preview_id": "replace-with-preview-kv-namespace-id"
  }
]
```

The placeholder IDs must be replaced with real IDs returned by:

```powershell
npx wrangler kv namespace create SETTINGS
npx wrangler kv namespace create SETTINGS --preview
```

## Local Validation Evidence

Environment:

```text
node --version -> v24.13.0
npm --version  -> 11.9.0
```

Install dependencies:

```powershell
cd .\labs\lab17\edge-api
npm install
```

Result:

```text
added 36 packages, and audited 37 packages
found 0 vulnerabilities
```

TypeScript validation:

```powershell
npm run typecheck
```

Result:

```text
> devops-edge-api@1.0.0 typecheck
> tsc --noEmit
```

Wrangler dry-run deployment:

```powershell
npm run deploy:dry-run
```

Result:

```text
wrangler 4.88.0
Total Upload: 3.57 KiB / gzip: 1.35 KiB

Binding                                                           Resource
env.SETTINGS (replace-with-production-kv-namespace-id)            KV Namespace
env.APP_NAME ("devops-edge-api")                                  Environment Variable
env.COURSE_NAME ("devops-core")                                   Environment Variable
env.DEPLOYMENT_ENV ("lab17")                                      Environment Variable

--dry-run: exiting now.
```

This proves the Worker source builds and Wrangler accepts the project structure. A real deploy still requires Cloudflare authentication, real KV namespace IDs, and secrets.

## Local Run Commands

```powershell
cd .\labs\lab17\edge-api
npm run dev
```

Route checks:

```powershell
Invoke-RestMethod http://127.0.0.1:8787/
Invoke-RestMethod http://127.0.0.1:8787/health
Invoke-RestMethod http://127.0.0.1:8787/edge
Invoke-RestMethod http://127.0.0.1:8787/config
Invoke-RestMethod http://127.0.0.1:8787/secrets
Invoke-RestMethod http://127.0.0.1:8787/counter
```

Expected `/health` response:

```json
{
  "status": "ok",
  "service": "devops-edge-api"
}
```

## Deployment Procedure

Authenticate:

```powershell
npx wrangler login
npx wrangler whoami
```

Create KV:

```powershell
npx wrangler kv namespace create SETTINGS
npx wrangler kv namespace create SETTINGS --preview
```

Create secrets:

```powershell
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

Deploy:

```powershell
npx wrangler deploy
```

Verify public URL:

```powershell
Invoke-RestMethod https://devops-edge-api.<subdomain>.workers.dev/health
Invoke-RestMethod https://devops-edge-api.<subdomain>.workers.dev/edge
Invoke-RestMethod https://devops-edge-api.<subdomain>.workers.dev/counter
```

Persistence check:

```powershell
Invoke-RestMethod https://devops-edge-api.<subdomain>.workers.dev/counter
npx wrangler deploy
Invoke-RestMethod https://devops-edge-api.<subdomain>.workers.dev/counter
```

The counter should continue increasing after redeploy because it is stored in Workers KV.

## Edge Metadata

The `/edge` endpoint returns Cloudflare request metadata supplied through `request.cf`.

Example response shape:

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

Exact values depend on the client network path and Cloudflare point of presence.

Workers run on Cloudflare's global edge automatically. I do not manually choose VM regions or deploy separate regional replicas; Cloudflare routes requests to an edge location and runs the Worker there.

Routing concepts:

- `workers.dev`: Cloudflare-managed public URL for fast deployment
- Routes: URL patterns on an existing Cloudflare zone
- Custom Domains: dedicated domain or subdomain assigned to a Worker

## Observability and Operations

The Worker logs each request:

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

Inspect deployments:

```powershell
npx wrangler deployments list
```

Rollback:

```powershell
npx wrangler rollback
```

Evidence to capture from a live Cloudflare account:

- deployed `workers.dev` URL
- `/edge` JSON response
- `/counter` value before and after redeploy
- `wrangler tail` log line
- Cloudflare dashboard metrics or deployment history screenshot

## Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
| --- | --- | --- |
| Setup complexity | Cluster, manifests, networking, controllers | Account, Worker config, bindings |
| Deployment speed | Image build, image pull, rollout | Usually seconds with Wrangler |
| Global distribution | Manual multi-region architecture | Automatic Cloudflare edge distribution |
| Cost for small apps | Cluster overhead exists | Low overhead and usage-based |
| State model | Volumes, databases, operators, services | KV, Durable Objects, D1, R2 bindings |
| Control | High runtime and networking control | More constrained runtime |
| Best use case | Long-running services and complex platforms | Lightweight APIs, routing, edge logic |

Kubernetes is better for long-running container workloads, custom runtimes, and complex stateful platforms. Workers are better for lightweight HTTP APIs, request routing, and globally distributed edge logic.

The main difference from Lab 2 is that this lab does not deploy a Docker image. The code targets the Workers runtime directly, and configuration, secrets, and state are provided through Cloudflare bindings.
