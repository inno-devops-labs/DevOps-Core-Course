# lab 17: cloudflare workers edge deployment

## 1. project setup

### cloudflare account & wrangler

| step | command | result |
|------|---------|--------|
| create project | `npm create cloudflare@latest -- edge-api` | worker only, typescript template |
| authenticate | `npx wrangler login` | browser-based OAuth |
| verify | `npx wrangler whoami` | account info |

### project structure

```
edge-api/
├── src/
│   └── index.ts           # worker entry point and routes
├── test/
│   ├── index.spec.ts      # vitest tests
│   ├── env.d.ts
│   └── tsconfig.json
├── .gitignore
├── .editorconfig
├── .prettierrc
├── package.json
├── tsconfig.json
├── vitest.config.mts
├── worker-configuration.d.ts  # auto-generated env types
└── wrangler.jsonc             # worker configuration
```

### why wrangler.jsonc over wrangler.toml

C3 now generates `wrangler.jsonc` by default. it supports json schema validation in editors and is the recommended format for new workers projects.

---

## 2. worker api implementation

### routes

| path | method | description |
|------|--------|-------------|
| `/` | GET | app information and endpoint listing |
| `/health` | GET | health check with timestamp |
| `/edge` | GET | edge metadata from `request.cf` |
| `/counter` | GET | KV-backed visit counter (persisted) |
| `/config` | GET | configuration info (vars and secrets status) |

### local development

```bash
npx wrangler dev
# starts at http://localhost:8787

# test routes
curl http://localhost:8787/health
curl http://localhost:8787/edge
curl http://localhost:8787/counter
```

### deployment

```bash
npx wrangler deploy
# output: https://edge-api.setanoier.workers.dev
```

### worker URL

| detail | value |
|--------|-------|
| url | `https://edge-api.setanoier.workers.dev` |
| subdomain | `setanoier` |
| primary region | automatic (all cloudflare PoPs) |

---

## 3. global edge behavior

### edge metadata endpoint

the `/edge` endpoint returns data from `request.cf`, which cloudflare populates at the edge:

```ts
if (url.pathname === "/edge") {
  return Response.json({
    colo: request.cf?.colo,
    country: request.cf?.country,
    city: request.cf?.city,
    asn: request.cf?.asn,
    httpProtocol: request.cf?.httpProtocol,
    tlsVersion: request.cf?.tlsVersion,
  });
}
```

### example response

[example /edge response](screenshots/edge-response.png)

expected fields:
- `colo` — cloudflare data center code (e.g., ARN = stockholm)
- `country` — caller's country from IP geolocation
- `asn` — autonomous system number of the caller's ISP

### how workers distributes globally

unlike fly.io or K8s where you manually choose regions, workers deploys to **all** cloudflare edge locations (~300+) simultaneously. there is no "deploy to 3 regions" step because:

1. the worker code is replicated to every cloudflare PoP automatically
2. requests are routed to the nearest data center by anycast DNS
3. the runtime isolates execution per-request — no warm VMs or containers needed

this contrasts with VM/PaaS platforms where you pick regions, provision machines, and manage capacity. workers trades control over placement for zero-configuration global reach.

### routing concepts

| concept | description |
|---------|-------------|
| `workers.dev` | free subdomain for quick access, no DNS setup needed |
| routes | attach worker to paths on an existing cloudflare zone |
| custom domains | make worker the origin for a domain/subdomain |

for this lab, `workers.dev` is used.

---

## 4. configuration, secrets & persistence

### environment variables

plaintext vars defined in `wrangler.jsonc`:

```jsonc
{
  "vars": {
    "APP_NAME": "devops-edge-api",
    "COURSE_NAME": "devops-core"
  }
}
```

**why plaintext vars are not suitable for secrets**: they are committed to git and visible in the dashboard and config file. anyone with repo access can read them.

### secrets

```bash
# set secrets (interactive prompt for values)
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL

# list secrets
npx wrangler secret list
```

secrets are encrypted at rest and only accessible via the `env` object at runtime. they never appear in `wrangler.jsonc` or git.

the `/config` endpoint demonstrates this — it shows whether secrets are set without exposing values:

```json
{
  "app_name": "devops-edge-api",
  "course_name": "devops-core",
  "admin_email_set": true,
  "api_token_set": true
}
```

### workers KV persistence

```bash
# create namespace
npx wrangler kv namespace create SETTINGS
# output: { id: "057ff4467ab5453f86baa507ccdd3de4" }
```

`wrangler.jsonc` binding:

```jsonc
{
  "kv_namespaces": [
    {
      "binding": "SETTINGS",
      "id": "057ff4467ab5453f86baa507ccdd3de4"
    }
  ]
}
```

### KV-backed counter

```ts
if (url.pathname === "/counter") {
  const raw = await env.SETTINGS.get("visits");
  const visits = Number(raw ?? "0") + 1;
  await env.SETTINGS.put("visits", String(visits));
  return Response.json({ visits });
}
```

### verifying persistence

after redeploying with `npx wrangler deploy`, the `/counter` value persists because KV data is independent of worker code deployments:

```bash
# before redeploy
curl https://edge-api.setanoier.workers.dev/counter
# {"visits":5}

npx wrangler deploy

# after redeploy
curl https://edge-api.setanoier.workers.dev/counter
# {"visits":6}
```

---

## 5. observability & operations

### logs

`console.log()` in the worker outputs to `npx wrangler tail`:

```ts
console.log("path", url.pathname, "colo", request.cf?.colo);
```

```bash
npx wrangler tail
# live stream of requests and logs
```

[example wrangler tail output](screenshots/wrangler-tail.png)

### metrics

[cloudflare dashboard - workers list](screenshots/dashboard-workers.png)

the cloudflare dashboard shows:
- request count per time period
- error rate (4xx, 5xx)
- CPU time per request
- subrequest counts

[cloudflare dashboard - metrics](screenshots/dashboard-metrics.png)

### deployments

```bash
# view deployment history
npx wrangler deployments list

# rollback to previous version
npx wrangler rollback
```

workers keeps version history, allowing instant rollbacks without re-deploying code.

---

## 6. kubernetes vs cloudflare workers comparison

| aspect | kubernetes | cloudflare workers |
|--------|------------|--------------------|
| setup complexity | high — cluster, networking, RBAC, ingress, cert management | low — `npm create cloudflare` and `wrangler deploy` |
| deployment speed | minutes (image pull, scheduling, rolling update) | seconds (code pushed to all edge PoPs) |
| global distribution | manual — choose regions, provision nodes, configure DNS routing | automatic — deploys to all ~300+ cloudflare locations |
| cost (for small apps) | $70+/mo for smallest managed cluster | free tier: 100k req/day, paid: $5/mo for 10M req |
| state/persistence model | persistent volumes, stateful sets, databases | KV (eventual consistency), durable objects, R2 |
| control/flexibility | full — any runtime, any config, any networking | limited — V8 isolate runtime, no long-running processes |
| best use case | complex microservices, enterprise compliance, stateful workloads | global APIs, edge logic, request transformation, lightweight services |

---

## 7. when to use each

### scenarios favoring kubernetes

- **enterprise compliance**: need fine-grained RBAC, audit logs, policy enforcement
- **stateful workloads**: databases, message queues, long-running processes
- **custom runtimes**: GPU inference, ML training, non-HTTP workloads
- **multi-team platform**: internal developer platform serving many teams
- **vendor independence**: must run on-prem or across cloud providers

### scenarios favoring cloudflare workers

- **global APIs**: low-latency endpoints close to users worldwide
- **request transformation**: auth, routing, A/B testing at the edge
- **cost-sensitive small apps**: free tier covers modest traffic
- **no ops overhead**: no servers, no scaling config, no patching
- **rapid prototyping**: from code to global URL in under a minute

### recommendation

for this project (a simple info API), cloudflare workers is the better fit: zero infrastructure management, instant global deployment, and the free tier is more than sufficient. kubernetes becomes necessary when you need persistent connections, complex state, or enterprise-grade control planes.

### reflection

- **easier than K8s**: no cluster management, no manifests, no ingress controllers. `wrangler deploy` replaces an entire CI/CD pipeline for simple apps.
- **more constrained**: no persistent filesystem, no long-running processes (10ms CPU limit on free tier), eventual-consistency-only KV. you cannot just "lift and shift" a docker container.
- **not a docker host**: the original python app from lab 2 cannot run here. the worker runtime is V8 isolates with typescript — a fundamentally different execution model. this required rewriting the API logic but the operational concepts (routes, health checks, secrets, state) map cleanly.

---

## 8. challenges

### regional connectivity

**problem**: `npx wrangler deploy` and `npx wrangler whoami` may fail with vague network errors from russia.

**cause**: cloudflare API endpoints may be partially restricted on some networks.

**solution**: use full-tunnel VPN. split-tunnel or proxy-only setups can leak wrangler traffic to the restricted network.

### KV namespace binding

**problem**: the KV namespace must be created before referencing it in `wrangler.jsonc`, but the worker code already expects the binding.

**solution**: create the namespace first with `npx wrangler kv namespace create SETTINGS`, then add the returned ID to `wrangler.jsonc`, then deploy.

### secret type declarations

**problem**: secrets are not declared in `wrangler.jsonc`, so `wrangler types` does not include them in the `Env` interface.

**solution**: manually add secret types to `worker-configuration.d.ts`:

```ts
interface Env {
  APP_NAME: "devops-edge-api";
  COURSE_NAME: "devops-core";
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}
```

note: this file is auto-generated, so changes may be overwritten by `npx wrangler types`. re-add secret types after regenerating.

---

## 9. key decisions

| question | answer |
|----------|--------|
| why typescript over javascript? | lab requirement; also provides type-safe access to `env` bindings |
| why `/config` endpoint? | demonstrates that secrets are accessible but their values are not exposed — only boolean presence |
| why KV over durable objects? | KV is simpler, free-tier eligible, and sufficient for a visit counter; durable objects add strong consistency at higher complexity |
| how does workers differ from docker-based PaaS? | no containers, no VMs, no port mapping — V8 isolates run request handlers at the edge with automatic scaling |
| what if the app needed a database? | would use hyperdrive (cloudflare's connection pooler) or an external DB via fetch, since workers cannot hold persistent connections |
