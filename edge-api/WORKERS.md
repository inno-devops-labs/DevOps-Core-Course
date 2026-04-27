# Lab 17 — Cloudflare Workers Edge Deployment

## 1. Deployment Summary

This lab implements and deploys a small serverless HTTP API using Cloudflare Workers. The application runs on Cloudflare's edge network and exposes several JSON endpoints for health checking, deployment metadata, edge request metadata, configuration validation, and KV-backed persistence.

### Worker URL

```text
https://edge-api.zagurskikhe.workers.dev
```

### Main Routes

| Route      | Method | Purpose                                                                                                      |
| ---------- | -----: | ------------------------------------------------------------------------------------------------------------ |
| `/`        |    GET | Returns general application information, version, platform, route list, and timestamp                        |
| `/health`  |    GET | Returns health status for operational checks                                                                 |
| `/edge`    |    GET | Returns Cloudflare edge metadata such as colo, country, ASN, HTTP protocol, and TLS version                  |
| `/config`  |    GET | Shows plaintext environment variables and confirms that secrets are configured without exposing their values |
| `/counter` |    GET | Increments and returns a persistent visit counter stored in Workers KV                                       |

### Configuration Used

The Worker uses the following Cloudflare Workers features:

| Feature          | Used For                                                  |
| ---------------- | --------------------------------------------------------- |
| `wrangler.jsonc` | Worker configuration                                      |
| Plaintext vars   | `APP_NAME`, `COURSE_NAME`                                 |
| Secrets          | `API_TOKEN`, `ADMIN_EMAIL`                                |
| Workers KV       | Persistent counter storage through the `SETTINGS` binding |
| `console.log()`  | Request logging for observability                         |
| `workers.dev`    | Public deployment URL                                     |

Plaintext variables are configured in `wrangler.jsonc`:

```json
"vars": {
  "APP_NAME": "edge-api",
  "COURSE_NAME": "devops-core"
}
```

Secrets are configured using Wrangler commands:

```powershell
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

Secret values are not committed to Git. They are accessed through the `env` object inside the Worker runtime.

Workers KV is configured with a namespace binding:

```json
"kv_namespaces": [
  {
    "binding": "SETTINGS",
    "id": "id"
  }
]
```

The `/counter` endpoint stores and retrieves the visits value from Workers KV.

---

## 2. Commands Used

### Project Creation

```powershell
npm create cloudflare@latest -- edge-api
cd edge-api
```

Selected options:

```text
Hello World example
Worker only
TypeScript
Git: Yes
Deploy now: No
```

### Authentication

```powershell
npx wrangler login
npx wrangler whoami
```

**Result:** Wrangler successfully authenticated with my Cloudflare account.

### Local Development

```powershell
npx wrangler dev
```

Local test URL:

```powershell
http://localhost:8787
```

### Local Route Tests

```powershell
curl.exe http://localhost:8787/
curl.exe http://localhost:8787/health
curl.exe http://localhost:8787/edge
curl.exe http://localhost:8787/config
curl.exe http://localhost:8787/counter
```

### KV Namespace Creation

```powershell
npx wrangler kv namespace create SETTINGS
```

The returned namespace ID was added to `wrangler.jsonc`.

### Secrets Creation

```powershell
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

### Deployment

```powershell
npx wrangler deploy
```

### Production Route Tests

```powershell
curl.exe https://edge-api.zagurskikhe.workers.dev/
curl.exe https://edge-api.zagurskikhe.workers.dev/health
curl.exe https://edge-api.zagurskikhe.workers.dev/edge
curl.exe https://edge-api.zagurskikhe.workers.dev/config
curl.exe https://edge-api.zagurskikhe.workers.dev/counter
```

### Logs

```powershell
npx wrangler tail
```

### Deployment History

```powershell
npx wrangler deployments list
```

### Rollback Command

```powershell
npx wrangler rollback
```

Rollback can be used to return the Worker to a previous deployed version.

---

## 3. Evidence

This section contains evidence that the Cloudflare Worker was deployed, tested, observed, and that its KV-backed persistence worked after redeployment.

## 3.1 Cloudflare Dashboard Screenshot

![](/docs/screenshots/dashboard.png)

Suggested screenshot contents:

## 3.2 Public Worker URL

My deployed Worker is available at:

```text
https://https://edge-api.zagurskikhe.workers.dev
```

## 3.3 `/health` Endpoint Evidence

Command used:

```powershell
curl.exe https://edge-api.zagurskikhe.workers.dev/health
```

Response from my deployment:

```json
{
  "status": "ok",
  "app": "edge-api",
  "version": "v1",
  "timestamp": "2026-04-27T16:45:33.532Z"
}
```

![](/docs/screenshots/health.png)

## 3.4 `/edge` Endpoint Evidence

Command used:

```powershell
curl.exe https://edge-api.zagurskikhe.workers.dev/edge
```

Response from my deployment:

```json
{
  "app": "edge-api",
  "version": "v1",
  "edge": {
    "colo": "LHR",
    "country": "GB",
    "city": "London",
    "region": "England",
    "asn": 63023,
    "httpProtocol": "HTTP/2",
    "tlsVersion": "TLSv1.3",
    "timezone": "Europe/London"
  },
  "note": "These fields are provided by Cloudflare at the edge. In local dev some values may be null.",
  "timestamp": "2026-04-27T16:46:30.883Z"
}
```

![](/docs/screenshots/edge.png)

This confirms that the Worker runs on Cloudflare's edge network and that Cloudflare provides request metadata through `request.cf`.

Important fields:

| Field | Meaning |
|---|---|
| `colo` | Cloudflare data center that handled the request |
| `country` | Country detected for the incoming request |
| `city` | City detected for the incoming request, if available |
| `asn` | Autonomous System Number of the client network |
| `httpProtocol` | HTTP protocol used by the request |
| `tlsVersion` | TLS version used for HTTPS |

## 3.5 `/config` Endpoint Evidence

Command used:

```powershell
curl.exe https://edge-api.zagurskikhe.workers.dev/config
```

Response from my deployment:

```json
{
  "appNameFromPlaintextVar": "edge-api",
  "courseNameFromPlaintextVar": "devops-core",
  "secrets": {
    "apiTokenConfigured": true,
    "adminEmailConfigured": true
  },
  "note": "Secret values are used through env but are not returned in the response."
}
```

![](/docs/screenshots/config.png)

This confirms that plaintext environment variables and secret bindings are available to the Worker through the `env` object.

The endpoint intentionally does not return the actual secret values.

## 3.6 `/counter` Endpoint Evidence

Command used for the request:

```powershell
curl.exe https://edge-api.zagurskikhe.workers.dev/counter
```

Response from my deployment:

```json
{
  "app": "edge-api",
  "key": "visits",
  "visits": 5,
  "persistedIn": "Workers KV",
  "timestamp": "2026-04-27T16:49:22.614Z"
}
```

![](/docs/screenshots/counter.png)

## 3.7 Persistence Verification After Redeploy

To verify persistence, I redeployed the Worker and called `/counter` again.

Redeploy command:

```powershell
npx wrangler deploy
```

Counter test command after redeploy:

```powershell
curl.exe https://edge-api.zagurskikhe.workers.dev/counter
```

Response after redeploy:

```json
{
  "app": "edge-api",
  "key": "visits",
  "visits": 6,
  "persistedIn": "Workers KV",
  "timestamp": "2026-04-27T16:51:31.004Z"
}
```

![](/docs/screenshots/redeploy.png)

The value continued increasing after redeployment. This confirms that the data is persisted in Workers KV and is independent from the deployed Worker code version.

## 3.8 Log Evidence

The Worker includes this logging statement:

```ts
console.log("request", {
  method: request.method,
  path,
  colo: request.cf?.colo,
  country: request.cf?.country,
});
```

Command used to view logs:

```powershell
npx wrangler tail
```

Command used in another terminal to generate a log entry:

```powershell
curl.exe https://edge-api.zagurskikhe.workers.dev/edge
```

![](/docs/screenshots/tail.png)

This confirms that request logs are emitted and can be inspected with Wrangler.

## 3.9 Metrics Evidence

Metric checked in the Cloudflare dashboard:

```text
Requests
```

Observation:

```text
The Cloudflare dashboard showed incoming requests after I tested the public workers.dev URL.
```

![](/docs/screenshots/requests.png)

Optional additional metrics:

```text
Errors
CPU time
Invocation count
```

![](/docs/screenshots/metrics.png)

## 3.10 Deployment History Evidence

Command used:

```powershell
npx wrangler deployments list
```

![](/docs/screenshots/list.png)

This confirms that at least two Worker deployments exist and that deployment history can be inspected.

## 3.11 Rollback Evidence

Rollback command:

```powershell
npx wrangler rollback
```

![](/docs/screenshots/rollback.png)

---

## 4. Kubernetes vs Cloudflare Workers Comparison

| Aspect                  | Kubernetes                                                                                                                                            | Cloudflare Workers                                                                                                                                   |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Setup complexity        | Higher. Requires cluster setup, manifests, services, ingress, container registry, and operational knowledge.                                          | Lower. Requires a Cloudflare account, Wrangler, and a Worker project.                                                                                |
| Deployment speed        | Slower. Images must be built, pushed, pulled, and rolled out to the cluster.                                                                          | Faster. Code is deployed directly to the Workers platform.                                                                                           |
| Global distribution     | Manual or platform-dependent. Multi-region deployment usually requires explicit configuration.                                                        | Built into the platform. Workers run on Cloudflare's global edge network.                                                                            |
| Cost for small apps     | Can be expensive because clusters or nodes may run continuously.                                                                                      | Often cheaper for small APIs because it is serverless and usage-based.                                                                               |
| State/persistence model | Supports many stateful patterns through databases, volumes, StatefulSets, and operators.                                                              | Worker execution is stateless by default. Persistent state uses platform bindings such as KV, D1, Durable Objects, or external services.             |
| Control/flexibility     | Very high. Supports almost any containerized workload, custom networking, background services, and long-running processes.                            | More constrained. Designed for request/response edge workloads and platform-supported bindings.                                                      |
| Best use case           | Complex backend systems, microservices, long-running services, internal platforms, custom infrastructure, and workloads needing full runtime control. | Lightweight APIs, edge routing, request transformation, globally distributed low-latency services, static-site backends, and simple serverless APIs. |

---

## 5. When to Use Each

### Scenarios Favoring Kubernetes

Kubernetes is a better choice when the application needs full control over the runtime environment, container images, networking, service discovery, background workers, internal services, or complex deployment topologies.

**Examples:**

```text
Large microservice platforms
Long-running backend services
Applications requiring custom binaries or OS-level dependencies
Stateful services with persistent volumes
Internal enterprise platforms
Complex CI/CD and progressive delivery workflows
```

### Scenarios Favoring Cloudflare Workers

Cloudflare Workers are a better choice when the application is lightweight, HTTP-based, globally distributed, and does not require a full container runtime.

**Examples:**

```text
Small public APIs
Edge authentication or request filtering
Webhook handlers
Redirect and routing logic
Low-latency globally distributed endpoints
Simple serverless applications
APIs that use Cloudflare KV, D1, Queues, or Durable Objects
```

### Recommendation

For this lab's application, Cloudflare Workers is the better fit. The application is a small HTTP API with health checks, JSON responses, edge metadata, configuration, secrets, and simple persistence. It does not need a Docker container, a long-running process, a Kubernetes Service, an Ingress controller, or manual region selection.

Kubernetes would be more appropriate if the application required multiple services, container-specific dependencies, custom networking, or more control over the runtime environment.

---

## 6. Reflection

The Workers deployment felt simpler than Kubernetes because I did not need to build and push a Docker image, write Kubernetes manifests, configure a Service, configure an Ingress, or manage a cluster. The deployment workflow was mostly handled through Wrangler.

The most convenient part was the `workers.dev` URL. It gave me a public endpoint without setting up DNS, ingress, or a load balancer.

The edge metadata was also useful because the platform automatically provided request context such as Cloudflare colo, country, HTTP protocol, and TLS version.

The main constraint is that Cloudflare Workers is not a Docker host. I cannot deploy an arbitrary container image from a previous lab. Instead, the application must be written for the Workers runtime. This changes the architecture: the Worker should be lightweight, request-driven, and stateless unless it uses a platform binding such as KV.

Another constraint is persistence. In Kubernetes, persistence might be handled by a database, a volume, or another service running in the cluster. In Workers, persistence is attached through platform services such as Workers KV. This is simpler for small use cases but less flexible than full infrastructure control.

Overall, Cloudflare Workers is a strong option for small globally distributed APIs and edge logic. Kubernetes is more powerful for complex systems, but it requires more operational work.
