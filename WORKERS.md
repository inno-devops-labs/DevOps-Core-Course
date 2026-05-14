# Lab 17 — Cloudflare Workers

## Deployment Summary

- Worker URL: https://lab17-worker.niyaz-lab17.workers.dev
- Main routes:
  - `GET /health` — health check
  - `GET /meta` — deployment metadata
  - `GET /edge` — edge request metadata
  - `GET /config` — configuration and secret binding status
  - `GET /kv?key=...` — read value from Workers KV
  - `POST /kv?key=...&value=...` — store value in Workers KV
  - `GET /` — route index
- Configuration used:
  - `wrangler.jsonc` with `PLAINTEXT_VAR`
  - KV binding: `LAB17_KV`
  - Secrets: `APP_SECRET_ONE`, `APP_SECRET_TWO`
  - Worker source: [lab17_worker/src/index.ts](lab17_worker/src/index.ts)
  - Wrangler config: [lab17_worker/wrangler.jsonc](lab17_worker/wrangler.jsonc)

## Evidence

### Cloudflare dashboard screenshot

Attach a screenshot from the Cloudflare dashboard showing the deployed Worker, request metrics, or deployment history.

Suggested filename:
- `screenshots/workers-dashboard.png`

### Example `/edge` JSON response

```json
{
  "buildVersion": "task5-v1",
  "worker": "lab17-worker",
  "route": "/edge",
  "colo": "MXP",
  "country": "FI",
  "city": "Helsinki",
  "asn": 210644,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3",
  "userAgent": "curl/8.5.0"
}
```

### Example log entry

Captured with `npx wrangler tail`:

```text
[task5-v1] Incoming request GET /meta
```

### Example metrics or deployment evidence

Deployment version IDs observed during this lab:
- `ac0607bf-9512-48b3-b155-6330c6016007`
- `7aecc901-4c93-4fef-b7b2-1e327587eb67`
- `215b9646-04de-4f3e-aa29-230b92776c26`

Current build after rollback:
- `task5-v1`

KV verification evidence:
- Stored key: `lab17-demo`
- Stored value: `hello-edge`
- Verified after redeploy: yes

## Kubernetes vs Cloudflare Workers Comparison

| Aspect | Kubernetes | Cloudflare Workers |
|---|---|---|
| Setup complexity | High: cluster, ingress, images, manifests, storage | Low: create Worker, deploy with Wrangler |
| Deployment speed | Slower, especially with image build/push and rollout | Very fast, usually seconds |
| Global distribution | Manual multi-region or extra tooling | Built in, automatic global edge network |
| Cost (for small apps) | Usually higher operational overhead | Usually lower and simpler for small apps |
| State/persistence model | Pods plus external storage, StatefulSets, PVCs | KV, Durable Objects, D1, R2, bindings |
| Control/flexibility | Very high | More constrained runtime and platform model |
| Best use case | Complex services, microservices, custom infrastructure | Small APIs, edge logic, global low-latency endpoints |

## When to Use Each

### Scenarios favoring Kubernetes

- Multiple cooperating services
- Heavy customization of runtime and networking
- Stateful workloads with strict control requirements
- Need for advanced scheduling, autoscaling, or service mesh features

### Scenarios favoring Workers

- Small HTTP APIs
- Edge-adjacent logic
- Global latency-sensitive endpoints
- Simple operational model without server management

### Recommendation

For this lab, Workers is the better fit because the app is a small HTTP API with simple configuration, edge metadata, and lightweight persistence. Kubernetes is preferable when the application needs full platform control, richer networking, or multi-service orchestration.

## Reflection

### What felt easier than Kubernetes?

- No container image build/push loop
- No cluster setup or ingress objects
- Faster deploy and rollback cycle
- Less operational overhead for configuration and routing

### What felt more constrained?

- Runtime is narrower than a full container environment
- Need to use platform bindings instead of arbitrary local disk state
- Fewer low-level infrastructure controls than Kubernetes

### What changed because Workers is not a Docker host?

- The app was written as a Worker-native HTTP service instead of a containerized server
- Persistent state moved to KV bindings instead of local volumes
- Configuration and secrets were handled through Wrangler bindings rather than environment files inside a container image


## Notes

- Custom domain setup was not required for this lab.
- The `workers.dev` URL is the required public deployment target.
- If you want to add more evidence, place screenshots in the repository and link them here.
