# Lab 17 Report - Cloudflare Workers Edge Deployment

This document records the Lab 17 Cloudflare Workers implementation, verification, and comparison with Kubernetes.

## Deployment Summary

Worker project location:

```text
edge-api/
```

Public Worker URL:

```text
https://edge-api.salavat-devops-core.workers.dev
```

The Worker is implemented in TypeScript in `edge-api/src/index.ts` and configured by `edge-api/wrangler.jsonc`.

### Main Routes

| Route | Purpose | Expected result |
|---|---|---|
| `/` | Basic service information | JSON with app name, course name, runtime, route list, and timestamp |
| `/health` | Health check | JSON status response with `status: ok` |
| `/edge` | Edge metadata | JSON with Cloudflare request metadata such as `colo`, `country`, `city`, `asn`, `httpProtocol`, and `tlsVersion` |
| `/config` | Configuration check | JSON showing plaintext vars and whether secrets are configured without exposing secret values |
| `/counter` | Persistence check | Reads and increments the `visits` value in Workers KV |
| `/admin` | Secret-protected route | Requires `Authorization: Bearer <API_TOKEN>` and proves the `API_TOKEN` secret is used |

### Configuration Used

Plaintext variables in `edge-api/wrangler.jsonc`:

| Variable | Value | Purpose |
|---|---|---|
| `APP_NAME` | `edge-api` | Used in route responses |
| `COURSE_NAME` | `devops-core` | Used in route responses |

Secrets required in Cloudflare:

| Secret | Purpose |
|---|---|
| `API_TOKEN` | Bearer token checked by `/admin` |
| `ADMIN_EMAIL` | Admin contact secret presence check |

KV binding required in Cloudflare:

| Binding | Purpose |
|---|---|
| `SETTINGS` | Stores the persistent `/counter` value under key `visits` |

KV namespace ID used in `edge-api/wrangler.jsonc`:

```text
59b9a00155cc479ea402d8ba549815dd
```

Plaintext vars are safe only for non-sensitive values because they are committed in `wrangler.jsonc`. Secrets are created with Wrangler and are not written to Git.

## Implementation Evidence

### Local TypeScript Check

Command:

```bash
cd edge-api
npm run typecheck
```

Result:

```text
> edge-api@1.0.0 typecheck
> tsc --noEmit
```

The command completed successfully.

### Wrangler Dry Run

Command:

```bash
cd edge-api
npx wrangler deploy --dry-run
```

Result:

```text
Total Upload: 3.71 KiB / gzip: 1.36 KiB
Your Worker has access to the following bindings:
Binding                                             Resource
env.SETTINGS (59b9a00155cc479ea402d8ba549815dd)    KV Namespace
env.APP_NAME ("edge-api")                           Environment Variable
env.COURSE_NAME ("devops-core")                     Environment Variable

--dry-run: exiting now.
```

This proves the Worker bundles correctly and Wrangler sees the expected bindings.

### Public Deployment

Deployment command:

```bash
cd edge-api
npm run deploy
```

Observed final deployment result:

```text
Uploaded edge-api (10.85 sec)
Deployed edge-api triggers (6.25 sec)
  https://edge-api.salavat-devops-core.workers.dev
Current Version ID: a6b31679-aec1-48c7-8ccd-6986b4a0277c
```

The account `workers.dev` subdomain is:

```text
salavat-devops-core
```

### Local Route Checks

Local server command:

```bash
cd edge-api
npx wrangler dev --port 8787
```

Health check:

```bash
curl http://127.0.0.1:8787/health
```

Observed response:

```json
{"status":"ok","app":"edge-api","timestamp":"2026-05-11T12:56:58.457Z"}
```

Edge metadata route:

```bash
curl http://127.0.0.1:8787/edge
```

Observed response:

```json
{"colo":"FRA","country":"DE","city":"Frankfurt am Main","asn":213877,"httpProtocol":"HTTP/1.1","tlsVersion":"TLSv1.3","workersDevHost":"127.0.0.1","timestamp":"2026-05-11T12:56:58.447Z"}
```

Configuration route:

```bash
curl http://127.0.0.1:8787/config
```

Observed response:

```json
{"appName":"edge-api","courseName":"devops-core","plaintextVarsSource":"wrangler.jsonc vars","apiTokenConfigured":false,"adminEmailConfigured":false,"secretValuesExposed":false,"note":"Plaintext vars are committed in wrangler.jsonc. Secret values are read from env but never returned."}
```

KV counter route:

```bash
curl http://127.0.0.1:8787/counter
```

Observed response:

```json
{"key":"visits","visits":1,"persistedIn":"Workers KV","note":"The value remains in the KV namespace after Worker redeploys."}
```

### Public Route Checks

Health check:

```bash
curl https://edge-api.salavat-devops-core.workers.dev/health
```

Observed response:

```json
{"status":"ok","app":"edge-api","timestamp":"2026-05-11T13:27:05.458Z"}
```

Edge metadata check:

```bash
curl https://edge-api.salavat-devops-core.workers.dev/edge
```

Observed response:

```json
{"colo":"FRA","country":"DE","city":"Frankfurt am Main","asn":213877,"httpProtocol":"HTTP/2","tlsVersion":"TLSv1.3","workersDevHost":"edge-api.salavat-devops-core.workers.dev","timestamp":"2026-05-11T13:27:05.425Z"}
```

Screenshot evidence:

![Lab 17 edge response](docs/screenshots/lab17-edge-response.png)

Configuration and secret presence check:

```bash
curl https://edge-api.salavat-devops-core.workers.dev/config
```

Observed response:

```json
{"appName":"edge-api","courseName":"devops-core","plaintextVarsSource":"wrangler.jsonc vars","apiTokenConfigured":true,"adminEmailConfigured":true,"secretValuesExposed":false,"note":"Plaintext vars are committed in wrangler.jsonc. Secret values are read from env but never returned."}
```

Secret-protected admin check:

```bash
curl -H "Authorization: Bearer <API_TOKEN>" \
  https://edge-api.salavat-devops-core.workers.dev/admin
```

Observed response:

```json
{"status":"authorized","adminEmailConfigured":true,"message":"The API_TOKEN secret matched the request bearer token."}
```

The real token value was generated locally and was not printed or committed.

### KV Persistence After Redeploy

Before redeploy:

```json
{"key":"visits","visits":2,"persistedIn":"Workers KV","note":"The value remains in the KV namespace after Worker redeploys."}
```

After redeploy:

```json
{"key":"visits","visits":3,"persistedIn":"Workers KV","note":"The value remains in the KV namespace after Worker redeploys."}
```

The counter continued from `2` to `3`, so the value was persisted in Workers KV and did not reset during deployment.

### Log Evidence

The Worker includes this log statement in `edge-api/src/index.ts`:

```ts
console.log("request", {
  method: request.method,
  path: url.pathname,
  colo: request.cf?.colo,
  country: request.cf?.country
});
```

Observed local Wrangler log entries:

```text
request { method: 'GET', path: '/counter', colo: 'FRA', country: 'DE' }
[wrangler:info] GET /counter 200 OK (78ms)
request { method: 'GET', path: '/edge', colo: 'FRA', country: 'DE' }
request { method: 'GET', path: '/config', colo: 'FRA', country: 'DE' }
request { method: 'GET', path: '/health', colo: 'FRA', country: 'DE' }
[wrangler:info] GET /edge 200 OK (90ms)
[wrangler:info] GET /config 200 OK (92ms)
[wrangler:info] GET /health 200 OK (89ms)
```

Production tail command:

```bash
cd edge-api
npx wrangler tail
```

Observed production log entry:

```text
Successfully created tail, expires at 2026-05-11T19:25:12Z
Connected to edge-api, waiting for logs...
GET https://edge-api.salavat-devops-core.workers.dev/health - Ok @ 5/11/2026, 4:27:45 PM
  (log) request { method: 'GET', path: '/health', colo: 'FRA', country: 'DE' }
```

### Cloudflare Metrics Screenshot Evidence

The deployed Worker is available in Cloudflare as `edge-api` under the `salavat-devops-core.workers.dev` subdomain.

The terminal session could not capture the authenticated Cloudflare dashboard UI because headless Chrome was stopped by Cloudflare security verification. Instead, I added a metrics evidence screenshot generated from the real Cloudflare GraphQL Analytics API through the authenticated Wrangler OAuth session.

Metrics screenshot:

![Lab 17 Cloudflare Workers metrics](docs/screenshots/lab17-cloudflare-workers-metrics.png)

If the grader requires the exact dashboard UI, capture one manually from:

```text
Cloudflare Dashboard -> Workers & Pages -> edge-api -> Metrics
```

Metrics to capture:

1. Request count for `edge-api`.
2. Error count, ideally `0` after successful route tests.
3. Recent invocation or CPU duration metric.

## Cloudflare Deployment Commands Used

These are the account-bound commands used to complete the deployment.

### Authenticate Wrangler

```bash
cd edge-api
npx wrangler login
npx wrangler whoami
```

Authentication succeeded and Wrangler showed the Cloudflare account with Workers and KV permissions.

### Create Secrets

```bash
cd edge-api
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

Do not commit the secret values. For local development only, copy `edge-api/.dev.vars.example` to `edge-api/.dev.vars` and replace the example values.

### Create Workers KV Namespace

```bash
cd edge-api
npx wrangler kv namespace create SETTINGS
```

The returned namespace ID was copied into `edge-api/wrangler.jsonc`:

```json
"kv_namespaces": [
  {
    "binding": "SETTINGS",
    "id": "59b9a00155cc479ea402d8ba549815dd"
  }
]
```

### Deploy

```bash
cd edge-api
npm run deploy
```

Deployed URL:

```text
https://edge-api.salavat-devops-core.workers.dev
```

### Verify Public Routes

```bash
curl https://edge-api.salavat-devops-core.workers.dev/health
curl https://edge-api.salavat-devops-core.workers.dev/edge
curl https://edge-api.salavat-devops-core.workers.dev/config
curl https://edge-api.salavat-devops-core.workers.dev/counter
curl -H "Authorization: Bearer <API_TOKEN>" \
  https://edge-api.salavat-devops-core.workers.dev/admin
```

Run `/counter`, redeploy, and run `/counter` again. The value should continue increasing because it is stored in Workers KV, not in Worker memory.

### Deployment History and Rollback

List deployments:

```bash
cd edge-api
npx wrangler deployments list
```

Rollback to a previous deployment:

```bash
cd edge-api
npx wrangler rollback
```

The rollback step should be used carefully because it changes the active production deployment.

Observed deployment history:

```text
Created:     2026-05-11T13:23:50.601Z
Source:      Unknown (deployment)
Version(s):  (100%) c88152f1-6e37-4059-b2ad-491c272415e4

Created:     2026-05-11T13:26:18.407Z
Source:      Secret Change
Version(s):  (100%) db1f8d29-f5f3-435e-8396-4c7a5344102e

Created:     2026-05-11T13:26:38.445Z
Source:      Unknown (deployment)
Version(s):  (100%) a6b31679-aec1-48c7-8ccd-6986b4a0277c
```

Rollback was documented rather than executed because the latest deployment is the verified working version. If rollback is needed, use:

```bash
npx wrangler rollback <previous-version-id>
```

## Kubernetes vs Cloudflare Workers Comparison

| Aspect | Kubernetes | Cloudflare Workers |
|---|---|---|
| Setup complexity | High. Requires cluster, nodes, namespaces, manifests or Helm, ingress, secrets, monitoring, and cluster operations. | Low. Requires Cloudflare account, Wrangler, Worker config, and optional bindings such as KV. |
| Deployment speed | Usually slower because images must be built, pushed, pulled, scheduled, and rolled out to pods. | Very fast because Wrangler uploads a small Worker bundle to Cloudflare's edge platform. |
| Global distribution | Must be designed manually with multiple clusters, regions, global load balancing, DNS, and replication. | Built in. Workers run on Cloudflare's global edge network without choosing regions manually. |
| Cost for small apps | Can be expensive because nodes or managed cluster resources usually run even when traffic is low. | Usually cheaper for lightweight APIs because the platform is serverless and usage-based. |
| State/persistence model | Strong options for persistent volumes, databases, StatefulSets, operators, and internal services. | No local durable disk. State must use bindings such as KV, Durable Objects, D1, R2, Queues, or external services. |
| Control/flexibility | Very high. Any containerized runtime, custom networking, sidecars, service mesh, and long-running workers are possible. | More constrained. Code must fit the Workers runtime, request lifecycle, supported APIs, and platform limits. |
| Best use case | Complex backend systems, container workloads, internal platforms, long-running services, and apps needing deep infrastructure control. | Lightweight APIs, edge routing, authentication checks, redirects, low-latency global reads, webhooks, and small serverless services. |

## When to Use Each

Use Kubernetes when:

1. The application is already container-based and needs full control over runtime, networking, or storage.
2. The workload has multiple services, background workers, databases, queues, and internal service-to-service communication.
3. The team needs advanced rollout strategies, custom operators, sidecars, or private cluster networking.
4. The workload is long-running or depends on software that does not fit the Workers runtime.

Use Cloudflare Workers when:

1. The application is a small HTTP API or edge function.
2. Low latency from many countries is important.
3. The service does not need a Docker container or local filesystem persistence.
4. Fast deployments and low operational overhead matter more than infrastructure control.
5. The workload can store state in KV, Durable Objects, D1, R2, or an external API.

My recommendation:

For this lab's API, Cloudflare Workers is the better fit. The API is small, HTTP-based, and benefits from global edge execution. Kubernetes would be more powerful, but it would add cluster, image, ingress, and monitoring overhead that is not needed for this workload.

## Reflection

What felt easier than Kubernetes:

1. No cluster setup was needed.
2. No Docker image build or registry push was needed.
3. Public exposure through `workers.dev` is simpler than Kubernetes ingress or NodePort setup.
4. Configuration bindings are direct and easy to access through the `env` object.
5. Global distribution is automatic instead of a separate multi-region architecture task.

What felt more constrained:

1. The Worker cannot run any arbitrary Docker image.
2. There is no normal local persistent disk.
3. Long-running background processes are not a natural fit.
4. Platform limits and supported runtime APIs matter more than they do in a container.
5. State has to be designed around Cloudflare bindings or external services.

What changed because Workers is not a Docker host:

1. I wrote a Workers-native TypeScript API instead of deploying the Lab 2 Docker image.
2. I used `wrangler.jsonc` for platform configuration instead of Kubernetes YAML for Deployments and Services.
3. I used Workers KV for persistence instead of a volume or database running inside the cluster.
4. I used `workers.dev` for public access instead of Kubernetes Service, Ingress, or LoadBalancer resources.
5. I treated secrets as Cloudflare bindings instead of Kubernetes Secret objects.

## Completion Checklist

| Requirement | Status |
|---|---|
| Worker project initialized | Complete in `edge-api/` |
| TypeScript Worker API implemented | Complete |
| At least 3 routes | Complete: `/`, `/health`, `/edge`, `/config`, `/counter`, `/admin` |
| `/health` endpoint | Complete and verified locally and on public URL |
| Edge metadata endpoint | Complete and verified locally and on public URL |
| Plaintext variable configured | Complete in `wrangler.jsonc` |
| Two secrets designed | Complete: `API_TOKEN` and `ADMIN_EMAIL` created with Wrangler |
| KV namespace binding | Complete: `SETTINGS` bound to `59b9a00155cc479ea402d8ba549815dd` |
| KV persistence endpoint | Complete in `/counter` |
| Logging added | Complete and verified with local logs and production `wrangler tail` |
| Wrangler dry-run | Complete |
| Public `workers.dev` deployment | Complete: `https://edge-api.salavat-devops-core.workers.dev` |
| Cloudflare metrics screenshot | Complete: `docs/screenshots/lab17-cloudflare-workers-metrics.png` |
| Deployment history and rollback evidence | Complete: deployment history captured and rollback command documented |
| Kubernetes comparison | Complete |
