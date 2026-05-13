# Lab 17 — Cloudflare Workers deployment write-up


## 1. Deployment summary

| Item | Value |
|------|--------|
| **Worker URL** | `https://edge-api.aidararchlinux.workers.dev/`|
| **Main routes** | See table below |
| **Configuration** | `wrangler.jsonc`: `vars` (`APP_NAME`, `COURSE_NAME`, `DEPLOYMENT_LABEL`), `kv_namespaces` binding `SETTINGS`, secrets `API_TOKEN`, `ADMIN_EMAIL` |

### Routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | App info (uses plaintext `vars`) |
| GET | `/health` | Health check |
| GET | `/meta` | Deployment-oriented JSON (labels, worker name, compatibility hint) |
| GET | `/edge` | Edge metadata: `colo`, `country`, `city`, `asn`, `httpProtocol`, `tlsVersion` |
| GET | `/counter` | KV-backed visit counter (key `visits`) |
| GET | `/admin/whoami` | Returns `ADMIN_EMAIL` when `Authorization: Bearer <API_TOKEN>` matches |

---

## 2. Evidence

1. **Cloudflare dashboard**.


2. **Example `/edge` JSON**:

   ```bash
   curl -sS "https://edge-api.aidararchlinux.workers.dev/edge"
   ```

   Paste JSON here:

   ```json
   {"colo":"VNO","country":"LT","city":"Vilnius","asn":215373,"httpProtocol":"HTTP/2","tlsVersion":"TLSv1.3"}
   ```

3. **Logs or metrics** — e.g. `npx wrangler tail` line or dashboard metrics screenshot.

---

## 3. Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|-------------------|
| **Setup complexity** | Cluster control plane, nodes, networking, ingress, often GitOps; high baseline effort. | Account + Wrangler + small script; no servers to patch. |
| **Deployment speed** | Image build, push, rollout, probes—minutes common. | Seconds; upload Worker bundle to edge. |
| **Global distribution** | Multi-region clusters, DNS, global load balancers—you design it. | Automatic; request runs in a PoP near the user unless you opt into placement features. |
| **Cost (small apps)** | Control plane + nodes or managed platform minimums add up. | Generous free tier; pay per request/storage bindings for small APIs. |
| **State/persistence model** | You bring PVCs, operators, DBs; clear long-lived process model. | Stateless isolate + platform stores (KV, D1, R2, etc.); not a general POSIX host. |
| **Control/flexibility** | Full OS, any binary, sidecars, kernel-level tuning. | V8 isolate limits, supported APIs, no arbitrary Docker image. |
| **Best use case** | Long-running services, heavy dependencies, batch, custom networking. | HTTP APIs, auth at edge, redirects, A/B, lightweight transforms close to users. |

---

## 4. When to use each

- **Favor Kubernetes** when you need containers, specific kernel/OS features, long-lived connections at scale you control, or stateful workloads that map naturally to pods and standard databases on your network.
- **Favor Workers** when you want a globally distributed HTTPS handler with minimal ops, low cold-start latency at the edge, and cost predictable for request-heavy but lightweight logic.
- **Recommendation:** Use Workers for this lab’s style of API; use Kubernetes when the workload is “my app is a bunch of containers with complex in-cluster dependencies.”

---

## 5. Reflection

- **Easier than Kubernetes:** No cluster lifecycle, no ingress controller tuning for a first public URL; `workers.dev` is immediate.
- **More constrained:** No Docker image from Lab 2; runtime is not a VM—you adapt to Workers APIs and binding model.
- **What changed without Docker:** You deploy a bundled script to Cloudflare’s runtime, not an image; persistence is explicit bindings (here, KV), not a container filesystem.

---

## 6. Global distribution

Workers runs your code in Cloudflare Points of Presence (PoPs) when a request arrives; the platform picks a location for that request rather than you selecting “deploy to `us-east`, `eu-west`, …” as separate steps. On VMs or many PaaS products you explicitly choose regions or replicate services. With Workers there is no separate “deploy to 3 regions” step because **the same version is available across the network** and execution follows traffic.

---

## 7. Routing: `workers.dev` vs Routes vs Custom Domains

- **`workers.dev`** — Quick public hostname `https://edge-api.aidararchlinux.workers.dev` for development and demos; no DNS zone required on your domain.
- **Routes** — Attach a Worker to URLs on a **zone already on Cloudflare** (path patterns, subdomains) so traffic to your existing site is handled by the Worker.
- **Custom Domains** — Serve your Worker as the origin for a hostname you control (often with TLS managed by Cloudflare). This lab uses **`workers.dev`** only; custom domains are optional.

---


## 8. Persistence verification 

1. Note current `/counter` value: `curl -sS "https://edge-api.aidararchlinux.workers.dev/counter"`. 
2. Run `npx wrangler deploy` again without deleting the KV namespace.
3. Hit `/counter` again — count should **continue** from the stored value (proves KV survives redeploy).
4. **What is stored:** KV key `visits` (string integer), incremented each GET `/counter`.
