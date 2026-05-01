# Lab 17 — Cloudflare Workers deployment (`edge-api`)

## 0. Manual steps (Cloudflare account — run on your machine)

1. **Sign up / log in** at [Cloudflare](https://dash.cloudflare.com/) and confirm **Workers & Pages** is available.
2. **CLI login:**  
   `cd edge-api && npx wrangler login`  
   Verify: `npx wrangler whoami`
3. **KV namespace:**  
   `npx wrangler kv namespace create SETTINGS`  
   Copy the **`id`** into `wrangler.jsonc` (replace `REPLACE_WITH_KV_NAMESPACE_ID`).  
   Optional for safer local testing:  
   `npx wrangler kv namespace create SETTINGS --preview`  
   and add `"preview_id": "<preview-id>"` on the same KV object in `wrangler.jsonc`.
4. **Secrets (≥2 — never commit values):**  
   `npx wrangler secret put API_TOKEN`  
   `npx wrangler secret put ADMIN_EMAIL`
5. **Local dev:** Copy `.dev.vars.example` → `.dev.vars`, edit values to match your secrets for local use; run `npm run dev`. Test with curl/browser on `http://127.0.0.1:8787`.
6. **Deploy:** `npm run deploy`. Save the printed **`workers.dev`** URL.
7. **Prod checks:** `curl .../health`, `curl .../edge`, `curl .../counter` twice (KV persists).
8. **`/admin`:**  
   `curl -sS -H "Authorization: Bearer YOUR_API_TOKEN" "https://.../admin"`
9. **Observability:** `npm run tail`; trigger traffic and capture one log line (or use dashboard metrics).
10. **Two deployments + rollback:** Change a small string or var, deploy again, run `npx wrangler deployments list`, then `npx wrangler rollback` (or use the dashboard).
11. **Evidence:** Fill section 2 in this file (paste `/edge` JSON), add screenshots, commit updates if your instructor expects them in-repo.

---

## 1. Deployment summary

| Item | Value |
|------|-------|
| **Public URL** | `https://edge-api.carrycsgo787.workers.dev` |
| **Worker name** | `edge-api` (see `wrangler.jsonc`) |

### Routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | App info using plaintext vars `APP_NAME`, `COURSE_NAME`. |
| GET | `/health` | Health check (`{ "status": "ok" }`). |
| GET | `/meta` | JSON deployment metadata (plaintext vars only). |
| GET | `/edge` | Edge **colo**, **country**, plus extra **city**, **asn**, **httpProtocol**, **tlsVersion** from `request.cf`. |
| GET | `/counter` | KV-backed counter (`SETTINGS` binding, key `visits`). |
| GET | `/admin` | Requires `Authorization: Bearer <API_TOKEN>`; returns message plus **ADMIN_EMAIL** (both Wrangler secrets). |

### Configuration

- **Plaintext vars** (`wrangler.jsonc` → `vars`): `APP_NAME`, `COURSE_NAME`.
- **Secrets** (Wrangler, not in Git): `API_TOKEN`, `ADMIN_EMAIL`.
- **KV**: binding `SETTINGS`; namespace ID pasted into `wrangler.jsonc` after creation.

---

## 2. Evidence (you must attach)

Paste or screenshot the following for grading:

### Dashboard

- [ ] Screenshot: Workers → **edge-api** overview (bindings / triggers visible).

### `/edge` JSON (production)

After deploy, run:

```bash
curl -sS "https://edge-api.carrycsgo787.workers.dev/edge"
```

Example production response (colo, country, and extra `request.cf` fields; values depend on where the request enters Cloudflare):

```json
{
  "colo": "ARN",
  "country": "FI",
  "city": "Helsinki",
  "asn": 56594,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3"
}
```

### Logs or metrics

- [ ] One line from `npx wrangler tail` **or** a screenshot of Workers metrics (requests/errors/latency).

---

## 3. Plaintext vars vs secrets

**Plaintext `vars`** are stored in configuration and are visible in the Cloudflare dashboard and in deployment metadata. They are fine for non-sensitive labels (`APP_NAME`, `COURSE_NAME`).

**Secrets** (`wrangler secret put`) are encrypted at rest, not committed to Git, and should hold credentials and private contact tokens (`API_TOKEN`, `ADMIN_EMAIL`).

---

## 4. Global distribution (short answers)

**How Workers runs globally:** Code is deployed to Cloudflare’s network; each request is handled at an edge POP near the client. The platform schedules an isolate close to the user instead of you picking VM regions.

**vs choosing regions:** On a VM/PaaS you pin deployments to regions (or replicas per region). Workers avoids a manual “deploy to three regions” step because **routing and execution placement are automatic** across Cloudflare’s POPs.

**Routing:**

| Mechanism | What it is |
|-----------|------------|
| **`workers.dev`** | Quick public hostname `https://<worker-name>.<account-subdomain>.workers.dev` (required for this lab). |
| **Routes** | Map URLs under a zone on Cloudflare (hostname/path patterns) to a Worker. |
| **Custom domains** | Attach your domain/subdomain so the Worker serves that hostname (optional here). |

---

## 5. Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|---------------------|
| **Setup complexity** | Higher (cluster, networking, manifests/Helm, ingress, RBAC). | Lower (CLI + dashboard; no servers to SSH into). |
| **Deployment speed** | Minutes typical (image pull, rollout); varies by registry/cluster. | Seconds for small bundles; edge propagation is fast. |
| **Global distribution** | You design replicas/CDNs/ingress per region unless paired with a global LB/CDN. | Built-in global edge execution per request. |
| **Cost (small apps)** | Cluster/node cost dominates even for tiny workloads; shared clusters amortize better. | Often cheap/free-tier friendly for low-traffic APIs; pay per requests/CPU bounds. |
| **State/persistence model** | StatefulSets, PVCs, managed DBs — mature patterns for durable state. | Ephemeral runtime; persistence via KV/D1/R2 etc., different consistency/latency trade-offs. |
| **Control/flexibility** | Full OS/process/container flexibility, sidecars, daemonsets, cron jobs on nodes. | Sandboxed V8 isolate limits (CPU/time, APIs); no arbitrary Docker images. |
| **Best use case** | Long-lived services, batch/cron on nodes, heavy dependencies, bespoke networking. | HTTP APIs at the edge, redirects, auth at edge, A/B, lightweight aggregation. |

### When to use each

- **Favor Kubernetes** when you need containers, persistent VMs, cluster-wide scheduling, GPU/long jobs, or strict intra-cluster networking.
- **Favor Workers** when you want low-latency HTTP handling worldwide with minimal ops and no Docker runtime requirement.

**Recommendation:** Use Workers for edge-shaped HTTP workloads; use Kubernetes when the workload is fundamentally container/process-centric or needs cluster primitives.

---

## 6. Reflection

| Question | Notes |
|----------|-------|
| **Easier than Kubernetes?** | No cluster provisioning; `wrangler deploy` and instant `workers.dev` URL; bindings wired in config. |
| **More constrained?** | No arbitrary Dockerfile; runtime limits; persistence models differ from PVCs + StatefulSets. |
| **Docker removed from picture** | You ship a Worker bundle (JS/TS), not an image; scaling and placement are platform-managed at the edge. |

---

## 7. Persistence checklist (lab Task 4)

- Stored value: KV key **`visits`** (incremented by **`GET /counter`**).
- **Verify after redeploy:** Deploy twice (`npx wrangler deploy`), hit `/counter`, confirm the counter **does not reset** to 1 unless you delete the KV key.

---

## 8. Observability & deployments (lab Task 5)

- Logging: `console.log` in `src/index.ts` (pathname, colo, method). Tail with:

  ```bash
  cd edge-api && npx wrangler tail
  ```

- **Two versions:** Change e.g. `APP_NAME` or a response string, deploy again; review history:

  ```bash
  npx wrangler deployments list
  ```

- **Rollback:**

  ```bash
  npx wrangler rollback
  ```

  Or rollback from the Workers dashboard (Versions / Deployments).
