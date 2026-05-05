# Lab 17 — Cloudflare Workers Edge Deployment

## 1. Deployment Summary

### Worker

- Worker name: `edge-api`
- Public URL: `https://edge-api.darriyano.workers.dev`
- Runtime: Cloudflare Workers
- Language: TypeScript
- State storage: Workers KV
- Workers subdomain: `darriyano.workers.dev`

The Worker was deployed to the public `workers.dev` domain using Wrangler.

Deployment command:

```bash
npx wrangler deploy
```

Deployment result:

```text
Uploaded edge-api
Deployed edge-api triggers
  https://edge-api.darriyano.workers.dev
Current Version ID: 42c30e09-be2d-4f26-b850-0af7b80ca323
```

After the redeploy used for persistence verification, the active deployment version was:

```text
edb884ca-4987-4106-93a6-f34e04e2f1de
```

---

## 2. Main Routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Returns application name, version, runtime, timestamp, and configuration status |
| GET | `/health` | Returns basic health status |
| GET | `/edge` | Returns Cloudflare edge metadata from the request context |
| GET | `/counter` | Increments and returns a persisted Workers KV counter |

---

## 3. Configuration

### Plaintext Variables

The following plaintext variables are configured in `wrangler.jsonc`:

```json
{
  "APP_NAME": "edge-api",
  "APP_VERSION": "1.0.1",
  "COURSE_NAME": "devops-core"
}
```

| Variable | Purpose |
|---|---|
| `APP_NAME` | Application name returned by `/` |
| `APP_VERSION` | Application version returned by `/` |
| `COURSE_NAME` | Course/lab identifier |

Plaintext variables are safe for non-sensitive configuration values, but they are not suitable for passwords, tokens, API keys, or private credentials because they are stored directly in project configuration and may be committed to Git.

### Secrets

Two secrets were configured with Wrangler:

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

Secret list output:

```json
[
  {
    "name": "ADMIN_EMAIL",
    "type": "secret_text"
  },
  {
    "name": "API_TOKEN",
    "type": "secret_text"
  }
]
```

The Worker uses the secrets through the `env` object. The API does not return secret values. It only reports whether the secrets are configured.

Production `/` response confirms that both secrets are available:

```json
"secretsConfigured": {
  "API_TOKEN": true,
  "ADMIN_EMAIL": true
}
```

### Workers KV

A KV namespace was created and bound to the Worker.

Binding in `wrangler.jsonc`:

```json
"kv_namespaces": [
  {
    "binding": "SETTINGS",
    "id": "1e2d0b529f0a4104bc9e7769936e1334"
  }
]
```

| Binding | KV Namespace ID | Purpose |
|---|---|---|
| `SETTINGS` | `1e2d0b529f0a4104bc9e7769936e1334` | Stores the persisted counter used by `/counter` |

The counter key used in KV is:

```text
visits
```

---

## 4. proof

### 4.1 Wrangler Authentication

Wrangler was authenticated using OAuth.

Command:

```bash
npx wrangler login
npx wrangler whoami
```

Result:

```text
Successfully logged in.

You are logged in with an OAuth Token, associated with the email android.stepanova@gmail.com.

Account Name: Android.stepanova@gmail.com's Account
Account ID: de299a463e35286b95650996b24c69cd
```

The OAuth token includes Workers and Workers KV permissions, including:

```text
workers:write
workers_kv:write
workers_scripts:write
workers_tail:read
```

---

### 4.2 Public Worker URL

Worker URL:

```text
https://edge-api.darriyano.workers.dev
```

The URL is available from the Cloudflare Dashboard under:

```text
Workers & Pages → edge-api
```

---

### 4.3 `/health` Endpoint

Command:

```bash
curl -fsS "$WORKER_URL/health" | jq
```

Response:

```json
{
  "status": "ok"
}
```

This confirms that the deployed Worker responds successfully on the public `workers.dev` URL.

---

### 4.4 `/` Endpoint

Command:

```bash
curl -fsS "$WORKER_URL/" | jq
```

Initial production response:

```json
{
  "app": "edge-api",
  "version": "1.0.0",
  "course": "devops-core",
  "runtime": "Cloudflare Workers",
  "timestamp": "2026-05-05T16:44:05.360Z",
  "config": {
    "plaintextVarsConfigured": {
      "APP_NAME": true,
      "APP_VERSION": true,
      "COURSE_NAME": true
    },
    "secretsConfigured": {
      "API_TOKEN": true,
      "ADMIN_EMAIL": true
    },
    "kvBindingConfigured": true
  }
}
```

After redeploy, the version was updated to `1.0.1`:

```json
{
  "app": "edge-api",
  "version": "1.0.1",
  "course": "devops-core",
  "runtime": "Cloudflare Workers",
  "timestamp": "2026-05-05T16:46:58.364Z",
  "config": {
    "plaintextVarsConfigured": {
      "APP_NAME": true,
      "APP_VERSION": true,
      "COURSE_NAME": true
    },
    "secretsConfigured": {
      "API_TOKEN": true,
      "ADMIN_EMAIL": true
    },
    "kvBindingConfigured": true
  }
}
```

This confirms:

- plaintext variables are configured;
- both secrets are available in production;
- the KV binding is available;
- redeployment updates the Worker version.

---

### 4.5 `/edge` Endpoint

Command:

```bash
curl -fsS "$WORKER_URL/edge" | jq
```

Response:

```json
{
  "colo": "ARN",
  "country": "RU",
  "city": "Perm",
  "asn": 12768,
  "asOrganization": "Real IP pool for individual PPPoE customers",
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3",
  "timezone": "Asia/Yekaterinburg"
}
```

This response confirms that the Worker receives Cloudflare edge metadata through the request context. The response includes the required fields:

- `colo`
- `country`
- `city`

It also includes additional fields:

- `asn`
- `asOrganization`
- `httpProtocol`
- `tlsVersion`
- `timezone`

---

### 4.6 `/counter` Endpoint

Command:

```bash
curl -fsS "$WORKER_URL/counter" | jq
curl -fsS "$WORKER_URL/counter" | jq
```

Responses:

```json
{
  "key": "visits",
  "previous": 0,
  "visits": 1,
  "persistedIn": "Workers KV",
  "timestamp": "2026-05-05T16:44:05.859Z"
}
```

```json
{
  "key": "visits",
  "previous": 1,
  "visits": 2,
  "persistedIn": "Workers KV",
  "timestamp": "2026-05-05T16:44:06.142Z"
}
```

This confirms that the `/counter` endpoint stores and updates state in Workers KV.

---

### 4.7 Persistence After Redeploy

To verify persistence, the application version was changed in `wrangler.jsonc`:

```json
"APP_VERSION": "1.0.1"
```

Then the Worker was redeployed:

```bash
npx wrangler deploy
```

After redeploy, `/counter` was called again.

Response after redeploy:

```json
{
  "key": "visits",
  "previous": 3,
  "visits": 4,
  "persistedIn": "Workers KV",
  "timestamp": "2026-05-05T16:46:58.682Z"
}
```

Conclusion: the counter value continued from the previous value instead of resetting to `1`. This confirms that the counter is persisted in Workers KV and is not stored in Worker process memory.

---

### 4.8 Deployment History

Command:

```bash
npx wrangler deployments list
```

Output:

```text
Created:     2026-05-05T16:27:53.297Z
Author:      android.stepanova@gmail.com
Source:      Upload
Message:     Automatic deployment on upload.
Version(s):  (100%) bbf801d1-7700-475e-b955-a99219eee9cb
                 Created:  2026-05-05T16:27:53.297Z
                     Tag:  -
                 Message:  -

Created:     2026-05-05T16:27:55.921Z
Author:      android.stepanova@gmail.com
Source:      Secret Change
Message:     -
Version(s):  (100%) c4d5dc66-8553-4755-9045-e3b4039d8626
                 Created:  2026-05-05T16:27:55.921Z
                     Tag:  -
                 Message:  -

Created:     2026-05-05T16:28:27.555Z
Author:      android.stepanova@gmail.com
Source:      Secret Change
Message:     -
Version(s):  (100%) 9b530969-d264-4c02-b387-b6395fd03e6f
                 Created:  2026-05-05T16:28:27.555Z
                     Tag:  -
                 Message:  -

Created:     2026-05-05T16:34:13.386Z
Author:      android.stepanova@gmail.com
Source:      Unknown (deployment)
Message:     -
Version(s):  (100%) 42c30e09-be2d-4f26-b850-0af7b80ca323
                 Created:  2026-05-05T16:34:10.283Z
                     Tag:  -
                 Message:  -

Created:     2026-05-05T16:46:22.069Z
Author:      android.stepanova@gmail.com
Source:      Unknown (deployment)
Message:     -
Version(s):  (100%) edb884ca-4987-4106-93a6-f34e04e2f1de
                 Created:  2026-05-05T16:46:19.516Z
                     Tag:  -
                 Message:  -
```

This confirms that deployment history was viewed and that multiple Worker versions/deployments exist.

Rollback procedure:

```text
To roll back, run `npx wrangler rollback`, select a previous stable deployment, confirm the operation, and then re-test `/health`, `/edge`, and `/counter`.
```

A rollback was not required for the final state, but the rollback procedure was reviewed.

---

### 4.9 Logs and Metrics

A console log statement was added to the Worker source code:

```ts
console.log(
  "request",
  JSON.stringify({
    path: url.pathname,
    method: request.method,
    colo: request.cf?.colo,
    country: request.cf?.country,
  }),
);
```

Logs were inspected with Wrangler:

```bash
npx wrangler tail
```

Wrangler successfully connected to the deployed Worker logs:

```text
Successfully created tail, expires at 2026-05-05T22:49:43Z
Connected to edge-api, waiting for logs...
```

The Cloudflare Dashboard can also be used to review Worker metrics:

```text
Cloudflare Dashboard → Workers & Pages → edge-api → Metrics
```

Metric reviewed:

```text
Requests and errors.
```

Observation:

```text
The Worker was invoked through curl requests to `/`, `/health`, `/edge`, and `/counter`. These requests can be reviewed in Cloudflare Workers logs or metrics.
```

---

## 5. proof Files

The `proof/` directory contains saved command outputs and API responses.



Commands used to generate proof:

```bash
mkdir -p proof

npx wrangler whoami > proof/00-whoami.txt

curl -fsS "$WORKER_URL/" | jq > proof/01-root.json
curl -fsS "$WORKER_URL/health" | jq > proof/02-health.json
curl -fsS "$WORKER_URL/edge" | jq > proof/03-edge.json
curl -fsS "$WORKER_URL/counter" | jq > proof/04-counter-before-redeploy.json

npx wrangler deployments list > proof/05-deployments.txt
npx wrangler secret list > proof/06-secrets-list.txt

curl -fsS "$WORKER_URL/counter" | jq > proof/07-counter-after-redeploy.json
```

---

## 6. Edge Distribution Explanation

Cloudflare Workers runs code on Cloudflare's global edge network. I did not manually select a server region or create multiple regional deployments. After deployment, the same Worker became available through the public `workers.dev` URL and requests were handled by Cloudflare's edge infrastructure.

The `/edge` endpoint demonstrates this behavior by returning request metadata such as `colo`, `country`, `city`, `asn`, and protocol information. In the observed production response, the Worker returned:

```json
{
  "colo": "ARN",
  "country": "RU",
  "city": "Perm"
}
```

This means that Cloudflare attached edge-specific request metadata to the request before it reached the Worker.

This differs from VM, Docker, or Kubernetes-based deployments. In those platforms, global distribution usually requires explicit configuration: multiple regions, clusters, load balancers, DNS routing, container registries, and deployment automation. With Workers, there is no separate "deploy to three regions" step because global edge execution is provided by the platform.

---

## 7. Routing Concepts

| Concept | Meaning |
|---|---|
| `workers.dev` | A Cloudflare-provided public URL for quickly exposing a Worker without owning a custom domain |
| Route | A rule that attaches a Worker to traffic for an existing Cloudflare-managed zone, such as `example.com/api/*` |
| Custom Domain | A user-owned domain or subdomain configured so that the Worker handles traffic directly under that hostname |

This lab uses `workers.dev` because it is the required public deployment target.

The deployed Worker URL is:

```text
https://edge-api.darriyano.workers.dev
```

Custom domain setup was not required for this lab.

---

## 8. Kubernetes vs Cloudflare Workers Comparison

| Aspect | Kubernetes | Cloudflare Workers |
|---|---|---|
| Setup complexity | Higher. Requires a cluster, manifests, services, networking, deployment objects, and often ingress configuration. | Lower. Requires a Workers project, Wrangler configuration, and a deploy command. |
| Deployment speed | Slower because the image must usually be built, pushed, pulled, and rolled out by the cluster. | Faster because the Worker code is uploaded directly to the Workers platform. |
| Global distribution | Requires explicit multi-region infrastructure or external global load balancing. | Built into the Cloudflare edge platform. |
| Cost for small apps | Can be inefficient because cluster resources may run continuously. | Usually more suitable for small HTTP APIs because the platform is request-driven. |
| State/persistence model | Supports databases, persistent volumes, StatefulSets, operators, and internal services. | Worker runtime is stateless; persistence must use platform services such as KV, D1, R2, Durable Objects, or external databases. |
| Control/flexibility | Very high. Kubernetes can run almost any containerized workload. | More constrained. The application must fit the Workers runtime model. |
| Best use case | Complex systems, long-running services, custom runtimes, stateful workloads, internal networking, and multi-service applications. | Lightweight APIs, edge logic, redirects, request filtering, globally distributed low-latency endpoints. |

---

## 9. When to Use Each

### Kubernetes is better when

Kubernetes is better when the application requires full control over the runtime, container images, networking, storage, service discovery, and long-running processes. It is also more suitable for complex systems made of many services, workloads that need custom binaries or system packages, and stateful backends that require stronger infrastructure control.

Examples:

- microservice platforms;
- internal backend systems;
- long-running workers;
- applications requiring custom containers;
- stateful services with persistent volumes;
- systems with complex networking or service mesh requirements.

### Cloudflare Workers is better when

Cloudflare Workers is better when the workload is a lightweight HTTP service that benefits from global edge execution and low operational overhead. It is suitable when the application can be stateless or can use Cloudflare-managed storage services such as KV.

Examples:

- small public APIs;
- health endpoints;
- request routing or rewriting;
- edge authentication checks;
- low-latency global endpoints;
- simple counters or configuration lookups using KV.

### Recommendation

For this lab, Cloudflare Workers is the better fit because the API is small, HTTP-based, globally reachable, and only needs simple persistence through Workers KV. Kubernetes would be excessive for this specific workload.

For larger backend systems, Kubernetes remains more flexible because it can run arbitrary containers and long-running workloads.

---

## 10. Reflection

### What felt easier than Kubernetes?

Deployment was easier than Kubernetes because there was no Docker image, registry, Kubernetes cluster, Service, Ingress, or rollout manifest. The public URL was created directly through the Workers platform.

The local-to-production workflow was also simpler:

```bash
npx wrangler dev
npx wrangler deploy
```

### What felt more constrained?

Workers is more constrained than Kubernetes because it is not a general-purpose Linux container. The application must fit the Workers runtime. Local filesystem persistence is not the right model. Long-running background processes and arbitrary system dependencies are also not handled the same way as in a container.

### What changed because Workers is not a Docker host?

The application was implemented as a Workers-native TypeScript API instead of a Dockerized service. Persistence was implemented using Workers KV instead of a local file, persistent volume, or Kubernetes StatefulSet. Configuration was handled through Worker bindings, plaintext variables, and Wrangler secrets instead of Kubernetes ConfigMaps and Secrets.

---

## 11. Final Checklist

| Checklist Item | Status |
|---|---|
| Cloudflare account created | Done |
| Workers project initialized | Done |
| Wrangler authenticated | Done |
| Worker deployed to `workers.dev` | Done |
| `/health` endpoint working | Done |
| Edge metadata endpoint implemented | Done |
| At least 1 plaintext variable configured | Done |
| At least 2 secrets configured | Done |
| KV namespace created and bound | Done |
| Persistence verified after redeploy | Done |
| Logs or metrics reviewed | Done |
| Deployment history viewed | Done |
| `WORKERS.md` documentation complete | Done |
| Kubernetes comparison documented | Done |
