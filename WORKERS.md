# Cloudflare Workers — Lab 17

This file satisfies **Task 6** in `labs/lab17.md`. The Worker source lives in [`edge-api/`](edge-api/) (TypeScript, Wrangler).

**You must fill in** URLs, raw `/edge` JSON, and screenshots after you authenticate and deploy with your Cloudflare account. **KV namespace ID** must replace the placeholder in `edge-api/wrangler.jsonc` before `wrangler deploy` succeeds.

---

## 1. Deployment summary (fill in)

| Field | Your value |
|-------|----------------|
| **Worker URL** | `https://________________.workers.dev` |
| **Worker name** (in `wrangler.jsonc`) | `edge-api` (change if you renamed) |
| **Main routes** | `GET /`, `GET /health`, `GET /meta`, `GET /edge`, `GET /counter` |
| **Plaintext vars** | `APP_NAME`, `COURSE_NAME` in `wrangler.jsonc` → `vars` |
| **Secrets** | `API_TOKEN`, `ADMIN_EMAIL` via `wrangler secret put` (see `edge-api/.dev.vars.example` for local) |
| **KV** | Binding `SETTINGS`; counter key `visits` |

### Setup commands (reference)

```bash
cd edge-api
npm install
npx wrangler login
npx wrangler whoami

# Create KV and paste the returned id into wrangler.jsonc → kv_namespaces[0].id
npx wrangler kv namespace create SETTINGS

npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL

npm run dev
npm run deploy
```

---

## 2. Evidence (paste / attach)

### Dashboard

- [ ] Screenshot: Workers & Pages → your Worker → overview or metrics.

### `/edge` JSON (public)

Paste one real response (proves `request.cf` at the edge):

```json
{
  "paste": "here"
}
```

### Logs or metrics

- [ ] Screenshot or paste one **log line** from `npx wrangler tail` (the Worker uses `console.log` per request).
- [ ] Note which **dashboard metric** you reviewed (e.g. requests, errors, CPU time).

### Deployments

- [ ] Ran **`npm run deploy`** (or `wrangler deploy`) at least **twice** after a small change.
- [ ] Ran **`npm run deployments`** (or `wrangler deployments list`) and captured output.
- [ ] **Rollback:** ran `npx wrangler rollback` **or** described equivalent rollback in the dashboard.

---

## 3. Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|--------|--------------|-------------------|
| **Setup complexity** | High: cluster lifecycle, networking, RBAC, add-ons. | Low: account + Wrangler; no nodes to manage. |
| **Deployment speed** | Image build, push, rollout across replicas. | Very fast bundling and global script rollout. |
| **Global distribution** | Multi-region clusters, DNS, and ingress design. | Automatic: runs close to eyeballs on Cloudflare’s network. |
| **Cost (small apps)** | Control-plane + node cost; often heavy for tiny APIs. | Generous free tier for modest traffic; pay per use beyond. |
| **State/persistence model** | PVCs, DBs, operators; familiar patterns. | KV, D1, R2, Durable Objects; not arbitrary POSIX disk. |
| **Control/flexibility** | Full Linux containers, arbitrary runtimes. | V8 isolate model: no Docker; CPU/time limits; constrained APIs. |
| **Best use case** | Mixed workloads, legacy apps, strict compliance, on-prem. | HTTP APIs, edge routing, auth at edge, static + light logic. |

---

## 4. When to use each

- **Kubernetes:** long-running containers, stateful systems, custom networking, teams already operating clusters.
- **Workers:** globally distributed HTTP handlers, low-latency edge logic, minimal ops, cost-sensitive small APIs.

**Recommendation:** Use **Workers** for stateless or KV-backed edge APIs; use **Kubernetes** when you need container fidelity, complex stateful stacks, or full control over the data plane.

---

## 5. Reflection (edit in your own words)

- **Easier than Kubernetes:** …
- **More constrained:** …
- **What changed without Docker:** …

---

## 6. Task 3 — Global edge (written summary)

**How Workers distributes globally:** Your script is deployed to Cloudflare’s edge; each request is handled in a nearby PoP using metadata like `colo` and `country` on `request.cf`.

**vs manual regions:** You do **not** pick three regions; the platform schedules execution per request. That removes “deploy to `ams` / `iad` / `sin`” style steps at the cost of less explicit placement control.

**Routing:** **`workers.dev`** is the quick public hostname (`<worker>.<subdomain>.workers.dev`). **Routes** attach a Worker to a hostname in a zone you control. **Custom domains** map your own DNS names to the Worker as origin.

---

## References

- [Workers overview](https://developers.cloudflare.com/workers/)
- [Wrangler](https://developers.cloudflare.com/workers/wrangler/)
- [Request `cf` properties](https://developers.cloudflare.com/workers/runtime-apis/request/#incomingrequestcfproperties)
- Course Kubernetes docs: `k8s/README.md`, `k8s/HELM.md`
