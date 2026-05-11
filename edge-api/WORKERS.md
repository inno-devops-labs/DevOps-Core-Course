# Lab 17 - Cloudflare Workers Edge Deployment

## 1. Deployment Summary

Worker project: `edge-api`

Implementation path:
- Source: `src/index.ts`
- Wrangler config: `wrangler.jsonc`
- Tests: `test/index.spec.ts`

Public Worker URL:
- `https://edge-api.forstandoff2-2-2.workers.dev`

Local development URL:
- `http://localhost:8787`

Routes:

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Deployment summary and route listing |
| `/health` | GET | Health check |
| `/edge` | GET | Cloudflare request metadata from `request.cf` |
| `/counter` | GET | Workers KV-backed persisted counter |
| `/config` | GET | Plaintext vars and secret binding status without leaking secret values |

Configuration used:
- Plaintext vars in `wrangler.jsonc`: `APP_NAME`, `COURSE_NAME`, `DEPLOYMENT_ENV`
- KV binding: `SETTINGS` -> `0ffbf5dc66ee44adacfc64be63312e3d`
- Secret bindings created with Wrangler: `API_TOKEN`, `ADMIN_EMAIL`
- Public route enabled with `workers_dev: true`

Plaintext vars are visible in the committed Wrangler config and should only contain non-sensitive settings. Secrets must be created with Wrangler so values are stored by Cloudflare and injected through `env` without being committed to Git.

## 2. Local Evidence

TypeScript check:

```text
npm run typecheck
tsc --noEmit
exit code: 0
```

Worker tests:

```text
npm test
Test Files  1 passed (1)
Tests       5 passed (5)
```

Final deployment:

```text
wrangler 4.90.0
Total Upload: 3.43 KiB / gzip: 1.27 KiB
Deployed edge-api triggers
https://edge-api.forstandoff2-2-2.workers.dev
Current Version ID: caaddfb0-29f1-43f0-9567-8965a527c3f9
```

Public route checks:

```text
GET https://edge-api.forstandoff2-2-2.workers.dev/health
HTTP/2 200
{"status":"ok","app":"edge-api","timestamp":"2026-05-11T15:16:03.183Z"}

GET https://edge-api.forstandoff2-2-2.workers.dev/edge
HTTP/2 200
{"colo":"CDG","country":"FR","city":"Paris","asn":56971,"httpProtocol":"HTTP/2","tlsVersion":"TLSv1.3","workerUrl":"https://edge-api.forstandoff2-2-2.workers.dev"}

GET https://edge-api.forstandoff2-2-2.workers.dev/counter
HTTP/2 200
{"key":"visits","visits":1,"persisted":true}

GET /counter again
{"key":"visits","visits":2,"persisted":true}

GET /counter after redeploy
{"key":"visits","visits":4,"persisted":true}

GET https://edge-api.forstandoff2-2-2.workers.dev/config
HTTP/2 200
{"appName":"edge-api","courseName":"devops-core","deploymentEnvironment":"production","secrets":{"apiTokenConfigured":true,"adminEmailConfigured":true},"kvBindingConfigured":true}
```

Example production log from `wrangler tail`:

```json
{
  "outcome": "ok",
  "scriptName": "edge-api",
  "scriptVersion": { "id": "74483171-f71b-4323-ba47-40b7810546ec" },
  "logs": [
    {
      "level": "log",
      "message": [
        "{\"event\":\"request\",\"path\":\"/edge\",\"method\":\"GET\",\"colo\":\"CDG\",\"country\":\"FR\"}"
      ]
    }
  ],
  "event": {
    "request": {
      "url": "https://edge-api.forstandoff2-2-2.workers.dev/edge",
      "method": "GET",
      "cf": {
        "colo": "CDG",
        "country": "FR",
        "city": "Paris",
        "httpProtocol": "HTTP/2",
        "tlsVersion": "TLSv1.3"
      }
    },
    "response": { "status": 200 }
  }
}
```

Dashboard evidence:
- Workers & Pages dashboard shows `edge-api` under account `7a1dd67ba958ede2f79d8d4d67c041e0`.
- Account subdomain is `forstandoff2-2-2.workers.dev`.
- Usage metrics panel shows request and CPU time counters for the Worker account.

## 3. Cloudflare Setup Commands Used

Authentication and account check:

```bash
npm exec wrangler -- login
npm exec wrangler -- whoami
```

KV namespace:

```bash
npm exec wrangler -- kv namespace create SETTINGS
```

Created namespace:

```text
binding = SETTINGS
id = 0ffbf5dc66ee44adacfc64be63312e3d
```

Secrets:

```bash
printf '%s' '<api-token-value>' | npm exec wrangler -- secret put API_TOKEN
printf '%s' '<admin-email-value>' | npm exec wrangler -- secret put ADMIN_EMAIL
```

Deployments:

```bash
npm run deploy
curl https://edge-api.forstandoff2-2-2.workers.dev/health
curl https://edge-api.forstandoff2-2-2.workers.dev/edge
curl https://edge-api.forstandoff2-2-2.workers.dev/counter
```

Operations:

```bash
npm exec wrangler -- tail edge-api --format=json
npm exec wrangler -- deployments list --name edge-api --json
npm exec wrangler -- rollback
```

Deployment history viewed with `wrangler deployments list`; latest entries include:

| Created | Trigger | Version |
|---|---|---|
| 2026-05-11T15:14:33Z | secret | `48e45fbe-0929-4eed-a637-ab3bd12e285b` |
| 2026-05-11T15:14:51Z | secret | `83878be3-d62d-470c-b6c8-da96b96fad7a` |
| 2026-05-11T15:15:29Z | deployment | `16bb6134-2d9c-4c3c-9203-b58fadb45d72` |
| 2026-05-11T15:17:06Z | deployment | `74483171-f71b-4323-ba47-40b7810546ec` |
| 2026-05-11T15:21:58Z | deployment | `caaddfb0-29f1-43f0-9567-8965a527c3f9` |

Rollback plan:
- `npm exec wrangler -- deployments list --name edge-api --json` identifies previous deployment versions.
- `npm exec wrangler -- rollback` can roll back to the previous version if the latest deployment breaks.
- I did not leave the Worker rolled back because the latest version is the intended working submission.

## 4. Edge Behavior

The `/edge` endpoint reads Cloudflare-provided request metadata from `request.cf`, including `colo`, `country`, `city`, `asn`, `httpProtocol`, and `tlsVersion`.

In production, this data is attached by Cloudflare at the edge location handling the request. Workers are deployed to Cloudflare's global network, so there is no separate "deploy to three regions" step. Cloudflare routes each request to its network automatically, while VM or many PaaS deployments usually require choosing regions, provisioning capacity, and managing traffic between those regions.

Routing concepts:

| Concept | Meaning |
|---|---|
| `workers.dev` | Cloudflare-provided public URL for a Worker, useful for this lab and quick deployments |
| Routes | Attach a Worker to matching traffic on an existing Cloudflare-managed zone |
| Custom Domains | Make a Worker respond directly for a chosen domain or subdomain |

## 5. Persistence

The `/counter` endpoint uses the `SETTINGS` KV namespace to store the `visits` key.

Public verification:
- Before final redeploy: `/counter` returned `{"key":"visits","visits":3,"persisted":true}`.
- After final redeploy: `/counter` returned `{"key":"visits","visits":4,"persisted":true}`.

KV is external state, so redeploying the Worker code did not delete values stored in the namespace.

## 6. Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|---|---|---|
| Setup complexity | High: cluster, nodes, ingress, registry, manifests, observability | Low: Worker project, Wrangler config, deploy |
| Deployment speed | Slower because images must build, push, pull, and roll out | Fast because code is uploaded to the Workers runtime |
| Global distribution | Requires multi-region clusters or external traffic management | Automatic on Cloudflare's global edge network |
| Cost for small apps | Can be expensive due to always-on cluster resources | Usually cheaper for small request-driven APIs |
| State/persistence model | Pods are ephemeral; state uses PVCs, databases, object stores | Worker is stateless; state uses bindings like KV, D1, R2, Durable Objects |
| Control/flexibility | Very high: custom containers, networking, sidecars, operators | More constrained runtime and platform APIs |
| Best use case | Complex services, custom runtimes, private networking, long-running workloads | Lightweight APIs, edge personalization, redirects, webhooks, latency-sensitive logic |

## 7. When to Use Each

Use Kubernetes when the application needs custom containers, long-running processes, complex service meshes, GPU or system-level dependencies, internal service networks, or strict control over deployment topology.

Use Cloudflare Workers when the workload is request-driven, stateless or binding-backed, latency-sensitive, globally accessed, and small enough to fit the Workers runtime model.

Recommendation for this lab: Workers is the better fit because the API is small, HTTP-native, and benefits from global edge execution without the operational weight of a Kubernetes cluster.

## 8. Reflection

Workers felt easier than Kubernetes for project setup, routing, local development, and deployment packaging. There is no container image, registry, cluster, ingress controller, or rollout manifest to maintain.

Workers felt more constrained because the runtime is not a Docker host. The application must be written for the Workers environment, and persistence must use platform bindings such as KV rather than local disk or container volumes.

The biggest mindset change is that deployment is code plus bindings, not an operating system image. Operational concerns still exist, but they move into Wrangler configuration, Cloudflare dashboard metrics, logs, versions, and bound services.
