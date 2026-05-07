# Cloudflare Workers — Deployment & Comparison

## 1. Deployment Summary

- **Worker URL:** `https://my-worker-api.damir-sadykov0407.workers.dev`  

- **Main Routes:**

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | General app info (name, course, environment, version, timestamp) |
| `/health` | GET | Health check – returns `{ status: "ok", timestamp }` |
| `/metadata` | GET | Deployment metadata (worker name, deployedAt, runtime) |
| `/edge` | GET | Edge metadata – colo, country, city, httpProtocol, tlsVersion, asn |
| `/secrets` | GET | Indicates whether secrets (`API_TOKEN`, `ADMIN_EMAIL`) are configured |
| `/counter` | GET | KV-backed counter – increments and returns visit count |
| `/hello/:name` | GET | Dynamic greeting (bonus) |

- **Configuration used (wrangler.jsonc):**
  - `name`: `my-worker-api`
  - `main`: `src/index.ts`
  - `compatibility_date`: `2025-04-01`
  - `vars`: plaintext variables (`APP_NAME`, `COURSE_NAME`)
  - `kv_namespaces`: binding `SETTINGS` for persistent counters
  - Secrets: `API_TOKEN`, `ADMIN_EMAIL` (set via `wrangler secret put`)

## 2. Evidence

Screenshot in `cloudflare/screenshots/` folder

### 2.2 Example `/edge` JSON Response

```bash
$ curl https://my-worker-api.damir-sadykov0407.workers.dev/edge
{"colo":"ARN","country":"LV","city":"Riga","httpProtocol":"HTTP/2","tlsVersion":"TLSv1.3","asn":56971,"timezone":"Europe/Riga"}
```

### 2.3 Example Log Entry (`wrangler tail`)

```
$ npx wrangler tail

 ⛅️ wrangler 4.88.0
───────────────────
Successfully created tail, expires at 2026-05-08T01:04:31Z
Connected to my-worker-api, waiting for logs...
GET https://my-worker-api.damir-sadykov0407.workers.dev/counter - Ok @ 5/7/2026, 10:05:34 PM
  (log) [2026-05-07T19:05:34.522Z] path: /counter, colo: ARN
GET https://my-worker-api.damir-sadykov0407.workers.dev/counter - Ok @ 5/7/2026, 10:05:36 PM
  (log) [2026-05-07T19:05:36.856Z] path: /counter, colo: ARN
^C
```

### 2.4 Metrics Screenshot

Screenshot in `cloudflare/screenshots/` folder

## 3. Kubernetes vs Cloudflare Workers Comparison

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| **Setup complexity** | High – requires cluster (minikube, EKS, etc.), networking, storage, helm, etc. | Low – a single `npm create cloudflare` command and `wrangler deploy`. |
| **Deployment speed** | Seconds to minutes (image pull, pod scheduling). | Sub‑second to a few seconds (code is pushed globally). |
| **Global distribution** | Manual – you choose regions and set up load balancers. | Automatic – code runs in >300 data centers worldwide. |
| **Cost (for small apps)** | Non‑trivial – cluster costs, node pricing, even for low traffic. | Extremely low – free tier (100k requests/day) and pay‑per‑use afterwards. |
| **State/persistence model** | Ephemeral pods + persistent volumes, databases, stateful sets. | Stateless by default; external services: KV, D1, R2, or external DB. |
| **Control/flexibility** | Full control – any container, any runtime, any OS configuration. | Restricted – only JavaScript/WebAssembly, limited system access, no arbitrary binaries. |
| **Best use case** | Complex microservices, long‑running processes, stateful apps, machine learning, legacy containers. | Lightweight APIs, edge logic, traffic routing, authentication, A/B testing, bots, static asset handling. |

## 4. When to Use Each

### Scenarios favoring Kubernetes
- You need to run a **generic container** (any language, any framework).
- Your application requires **stateful storage** or **long‑running connections** (WebSockets, gRPC streams).
- You need **GPU** or specialised hardware.
- You already have a large microservices architecture and teams familiar with k8s.
- You require full control over network policies, security, and node configuration.

### Scenarios favoring Cloudflare Workers
- You want a **global API** with low latency at the edge (e.g., personalisation, geolocation, bot detection).
- You need **serverless** scaling with zero cold starts (for most regions).
- Your workload is **event‑driven** or **HTTP‑based** and stateless.
- You are on a **tight budget** or building a small hobby project.
- You want to **avoid infrastructure management** completely.

### My recommendation
- **For this course (learning DevOps):** Both are valuable. Kubernetes teaches deep infrastructure skills; Workers teaches edge serverless paradigms.
- **For a production decision:** Use Kubernetes for your core, complex, stateful services. Use Workers for global edge logic, API gateways, and high‑performance, low‑latency endpoints that need to be close to users – and combine them (e.g., Workers as a reverse proxy in front of a k8s backend).

## 5. Reflection

### What felt easier than Kubernetes?
- **Deployment** – one command (`wrangler deploy`) and the code is live globally. No building images, pushing to registry, writing YAML, or waiting for pods.
- **Logging and debugging** – `wrangler tail` gives instant real‑time logs without needing to set up Fluentd or Loki.
- **Local development** – `wrangler dev` runs the Worker locally with hot reload, no `minikube` or Docker required.
- **Secrets management** – `wrangler secret put` is dead simple.
- **Global reach** – zero effort to be on every continent.

### What felt more constrained?
- **Runtime environment** – Only JavaScript/TypeScript (or Wasm). You cannot run a Python Flask app, a Go binary, or a database inside a Worker.
- **Stateless by default** – To store anything, you must call an external service (KV, D1, R2). You can’t just write to a local file or use in‑memory state across requests.
- **Execution limits** – Free tier limits CPU time (10 ms for unbound?), maximum subrequest count, etc. A complex operation may need to be split into multiple workers or deferred with Queues.
- **No arbitrary system calls** – You can’t run `iptables`, `mount`, or shell commands. Everything must be pure JavaScript.

### What changed because Workers is not a Docker host?
- **No container image** – You deploy code directly, not an image with OS layers. This makes deployments extremely fast but also limits what you can bundle (no `apt-get install`, no compiled binaries unless compiled to Wasm).
- **No filesystem persistence** – You can’t rely on writing to `/tmp` or using a persistent volume. The only safe storage is KV, D1, or external APIs.
- **Cold start perception** – In Workers, cold starts are extremely rare (often <5ms) compared to containers. You don’t need to keep a “warm” instance.
- **Security model** – Each Worker runs in an isolate (not a process). Memory and CPU are isolated, but you cannot inspect the underlying OS.

Overall, Workers feels like “serverless done right” for HTTP APIs, while Kubernetes remains the king for full‑fledged applications. Both have their place in a modern cloud toolkit.

---
