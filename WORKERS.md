# Lab 17 — Cloudflare Workers (`WORKERS.md`)

**Public Worker URL:** `https://edge-api.k141-929b5b89-lab17.workers.dev`  
**Account `workers.dev` subdomain:** `k141-929b5b89-lab17.workers.dev`  

---

## 1. Task 1

### Account & Workers access

- Cloudflare account in use (Wrangler OAuth): `**kirillefimovic141@gmail.com`**, Account ID `**3e5b74fa69b8a99bc4d36989f51eb87b`** 
- Workers are reachable in the dashboard at:  
`https://dash.cloudflare.com/3e5b74fa69b8a99bc4d36989f51eb87b/workers`

### `workers.dev` subdomain

Each account can use `**https://<worker-name>.<account-subdomain>.workers.dev`**. This project uses `**edge-api`** on subdomain `**k141-929b5b89-lab17**`. See [Workers dev routing](https://developers.cloudflare.com/workers/configuration/routing/workers-dev/).

### Project creation (C3)

Project scaffold (already in repo):

```bash
npm create cloudflare@latest edge-api
# Hello World → Worker only → TypeScript → deploy: No (then iterate)
```

### `wrangler.jsonc` (role)

Single source of truth for Wrangler: **Worker name**, `**main` entry**, `**compatibility_date`**, `**workers_dev`**, observability, plaintext `**vars**`, **KV bindings**, etc. Used by `wrangler dev`, `wrangler deploy`, `wrangler tail`, `wrangler secret put`, and `wrangler kv` commands.

### Bindings (concepts)

- `**vars`**: plaintext, versioned with the repo — **not for secrets**.
- **Secrets**: stored in Cloudflare for the Worker; exposed as `env.SECRET_NAME` at runtime; **never committed**.
- **KV**: namespace in the account; bound by **namespace id** in `wrangler.jsonc`; durable across redeploys.

`npx wrangler whoami` 

```text
 ⛅️ wrangler 4.90.1
───────────────────
Getting User settings...
👋 You are logged in with an OAuth Token, associated with the email kirillefimovic141@gmail.com.
┌───────────────────────────────────────┬──────────────────────────────────┐
│ Account Name                          │ Account ID                       │
├───────────────────────────────────────┼──────────────────────────────────┤
│ Kirillefimovic141@gmail.com's Account │ 3e5b74fa69b8a99bc4d36989f51eb87b │
└───────────────────────────────────────┴──────────────────────────────────┘
```
---

## 2. Task 2

### 2.1 Routes (≥3 + `/health` + deployment JSON)


| Method | Path       | Response                                                 |
| ------ | ---------- | -------------------------------------------------------- |
| GET    | `/`        | App JSON (`APP_NAME`, `COURSE_NAME`, message, timestamp) |
| GET    | `/health`  | `{ "status": "ok" }`                                     |
| GET    | `/deploy`  | Deployment / app metadata JSON                           |
| GET    | `/edge`    | `request.cf` edge metadata JSON                          |
| GET    | `/secrets` | Redacted proof secrets are bound                         |
| GET    | `/counter` | KV-backed `visits` counter                               |
| *      | other      | `404`                                                    |


### 2.2 Local run

```bash
cd edge-api
npx wrangler dev --port 8787
# other terminal:
curl -sS http://localhost:8787/health
curl -sS http://localhost:8787/edge
```

Bindings table (local dev; KV uses local store under `.wrangler/`):

```text
Your Worker has access to the following bindings:
Binding                                                 Resource                  Mode
env.SETTINGS (00000000000000000000000000000001)         KV Namespace              local
env.APP_NAME ("edge-api")                               Environment Variable      local
env.COURSE_NAME ("devops-core")                         Environment Variable      local
```

> Note: production KV binding uses the **real** namespace id in `wrangler.jsonc` (`3dcb6d1c6aa540479de2b3a7b0556cd2`); local dev   show a placeholder id in the table depending on Wrangler version - I had some network issues.

### 2.3 Automated tests

```bash
cd edge-api && npm test -- --run
```

Output (excerpt):

```text
stdout | test/index.spec.ts > edge-api worker > GET / returns JSON app info (unit style)
request { path: '/', method: 'GET', colo: undefined, country: undefined }

stdout | test/index.spec.ts > edge-api worker > GET /health (integration style)
request { path: '/health', method: 'GET', colo: undefined, country: undefined }

 ✓ test/index.spec.ts (2 tests) 160ms
 Test Files  1 passed (1)
```

### 2.4 Deploy + public URL

```bash
cd edge-api && npm run deploy
```

**Live URL:** `https://edge-api.k141-929b5b89-lab17.workers.dev`

---

## 3. Task 3

### 3.1 `/edge` implementation

Returns `**colo`**, `**country`**, plus `**city**`, `**asn**`, `**httpProtocol**`, `**tlsVersion**` from `request.cf`.

### 3.2 Public `/edge` JSON (copy-paste — **real edge**)

Commands:

```bash
curl -sS "https://edge-api.k141-929b5b89-lab17.workers.dev/health"
curl -sS "https://edge-api.k141-929b5b89-lab17.workers.dev/edge"
```

Observed output:

```text
{"status":"ok"}
{"colo":"HEL","country":"RU","city":"Innopolis","asn":203509,"httpProtocol":"HTTP/2","tlsVersion":"TLSv1.3"}
```

### 3.3 Global distribution

Traffic enters a nearby **PoP**; the Worker runs on the edge that handles the request — you **do not** pick three regions like many VMs/PaaS. Same script version is available across the network; execution follows eyeballs. See [How Workers works](https://developers.cloudflare.com/workers/reference/how-workers-works/).

### 3.4 Routing: `workers.dev` vs Routes vs Custom Domains


| Mechanism          | Purpose                                                                                                                    |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `**workers.dev`**  | Quick public URL `https://<worker>.<subdomain>.workers.dev` (used for this lab).                                           |
| **Routes**         | Attach Worker to URLs on a **Cloudflare zone** you control.                                                                |
| **Custom Domains** | Worker as origin for a hostname ([docs](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/)). |


---

## 4. Task 4

### 4.1 Plaintext `vars` (and why not for secrets)

In `[edge-api/wrangler.jsonc](edge-api/wrangler.jsonc)`:

```json
"vars": {
  "APP_NAME": "edge-api",
  "COURSE_NAME": "devops-core"
}
```

Used in `/`, `/deploy`, etc. **Plaintext vars are wrong for secrets** because they live in Git, Wrangler config history, and the dashboard — anyone with repo or account access can read them.

### 4.2 Secrets (≥2), not in Git

```bash
cd edge-api
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

Used in code via `env.API_TOKEN` and `env.ADMIN_EMAIL`. `**/secrets` returns only non-sensitive tails**

### 4.3 KV namespace + binding

`npx wrangler kv namespace list`:

```json
[
  {
    "id": "3dcb6d1c6aa540479de2b3a7b0556cd2",
    "title": "SETTINGS",
    "supports_url_encoding": true
  }
]
```

Bound in `wrangler.jsonc` as `SETTINGS` → id `**3dcb6d1c6aa540479de2b3a7b0556cd2**`.

### 4.4 Persistence (`visits`)

- **Stored key:** `visits` (string integer), incremented on each `GET /counter`.
- **Proof after multiple deploys:** KV is account storage; counter does not reset on redeploy. Example **two consecutive** production calls:

```bash
curl -sS "https://edge-api.k141-929b5b89-lab17.workers.dev/counter"
curl -sS "https://edge-api.k141-929b5b89-lab17.workers.dev/counter"
```

```text
{"visits":6,"storedKey":"visits"}
{"visits":7,"storedKey":"visits"}
```

Further hits keep incrementing 

---

## 5. Task 5

### 5.1 Logs (`console.log` + tail)

Source logs in `[edge-api/src/index.ts](edge-api/src/index.ts)`:

```ts
console.log("request", {
  path: url.pathname,
  method: request.method,
  colo: cf?.colo,
  country: cf?.country,
});
```

```text
request { path: '/health', method: 'GET', colo: undefined, country: undefined }
```

### 5.2 Metrics (dashboard)

**Metric reviewed:** **Request count** (and optionally **Errors**) for Worker `**edge-api`** in **Workers & Pages → edge-api → Metrics** in the Cloudflare dashboard. After hitting `/health` and `/counter`, request count should increase — confirms invocations reached the edge.

### 5.3 Multiple deploys + history

At least **two** production deploys were performed (initial publish with `workers.dev` onboarding, then a second deploy with message `lab17 second deploy v2 message` and home JSON text `— v2`). Example second-deploy footer:

```text
Deployed edge-api triggers (5.86 sec)
  https://edge-api.k141-929b5b89-lab17.workers.dev
Current Version ID: ba6daceb-e38b-4e16-a954-84807e7bf921
```

`**npx wrangler deployments list**` (excerpt captured when API was reachable; **re-run locally** for a fresh timestamped full log):

```text
Created:     2026-05-12T20:11:29.365Z
Author:      kirillefimovic141@gmail.com
Source:      Secret Change
Version(s):  (100%) e08b3812-6b21-406c-b9bb-32b7da980a6b

Created:     2026-05-12T20:11:50.239Z
Author:      kirillefimovic141@gmail.com
Source:      Unknown (deployment)
Version(s):  (100%) fd17e152-834f-4d65-9310-235b85c4f924

Created:     2026-05-12T20:18:34.144Z
Author:      kirillefimovic141@gmail.com
Source:      Unknown (deployment)
Version(s):  (100%) e18634b4-cf64-4ed8-934b-c0f6e86254dc

Created:     2026-05-12T20:19:11.981Z
Author:      kirillefimovic141@gmail.com
Source:      Unknown (deployment)
Version(s):  (100%) 10a1b5a6-57cb-4e36-9365-b8687090e6a3

Created:     2026-05-12T20:20:20.866Z
Author:      kirillefimovic141@gmail.com
Source:      Unknown (deployment)
Version(s):  (100%) ae924f3a-a962-42c6-b567-f33736fca7ad
```

### 5.4 Rollback

Lab allows describing rollback.Example prior version id from history above: `**ae924f3a-a962-42c6-b567-f33736fca7ad**`. Rolling back temporarily switches traffic to that bundle; redeploy restores the newest version.

---

## 6. Task 6 

Full production `curl` suite 

```bash
BASE='https://edge-api.k141-929b5b89-lab17.workers.dev'
curl -sS "$BASE/health" && echo
curl -sS "$BASE/" && echo
curl -sS "$BASE/deploy" && echo
curl -sS "$BASE/edge" && echo
curl -sS "$BASE/secrets" && echo
curl -sS "$BASE/counter" && echo
curl -sS -o /dev/null -w "nope HTTP %{http_code}\n" "$BASE/nope"
```

Output:

```text
{"status":"ok"}
{"app":"edge-api","course":"devops-core","message":"Hello from Cloudflare Workers (Lab 17) — v2","timestamp":"2026-05-12T21:17:10.457Z"}
{"app":"edge-api","course":"devops-core","runtime":"cloudflare-workers","compatibilityDate":"2026-03-10","deployment":{"note":"Metadata about this deployment surface; version id is available in dashboard / wrangler deployments.","timestamp":"2026-05-12T21:17:10.699Z"}}
{"colo":"HEL","country":"RU","city":"Innopolis","asn":203509,"httpProtocol":"HTTP/2","tlsVersion":"TLSv1.3"}
{"apiTokenTail":"…only","adminEmailDomain":"gmail.com"}
{"visits":8,"storedKey":"visits"}
nope HTTP 404
```

| Route      | PNG                                       |
| ---------- | ----------------------------------------- |
| `/`        | [/](docs/lab17/worker-root.png)           |
| `/health`  | [/health](docs/lab17/worker-health.png)   |
| `/edge`    | [/edge](docs/lab17/worker-edge.png)       |
| `/deploy`  | [/deploy](docs/lab17/worker-deploy.png)   |
| `/secrets` | [/secrets](docs/lab17/worker-secrets.png) |
| `/counter` | [/counter](docs/lab17/worker-counter.png) |




---

## 7. Kubernetes vs Cloudflare Workers (Task 6 table)


| Aspect                      | Kubernetes                                                                      | Cloudflare Workers                                                |
| --------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| **Setup complexity**        | Cluster control plane, networking, RBAC, ingress, often GitOps — high baseline. | Account + Wrangler + small project; no servers to SSH into.       |
| **Deployment speed**        | Image build, push, rollout, probes — minutes common.                            | Often seconds: upload script + config to edge.                    |
| **Global distribution**     | You design multi-region replicas, DNS, and traffic steering.                    | Automatic: runs near the PoP handling the request.                |
| **Cost (small apps)**       | Control plane + nodes or managed cluster cost even when idle.                   | Generous free tier for low traffic; pay per use at scale.         |
| **State/persistence model** | PVs, operators, self-managed or cloud DBs.                                      | KV, R2, Durable Objects, Hyperdrive — platform primitives.        |
| **Control/flexibility**     | Full Linux containers, any binary, sidecars.                                    | Sandboxed isolate; CPU/time limits; not a general container host. |
| **Best use case**           | Long-running services, heavy dependencies, batch, cluster-wide ops.             | HTTP APIs, edge auth, routing, caching, lightweight transforms.   |


### When to use each

- **Kubernetes:** container-shaped workloads, strict OS/library needs, long CPU, in-cluster batch, existing platform teams.
- **Workers:** globally fronted HTTP/APIs, minimal ops, edge latency-sensitive handlers.

**Recommendation:** Workers for this lab’s API; Kubernetes when the workload is inherently container-native and needs cluster-level control.

---

## 8. Reflection (Task 6)

- **Easier than Kubernetes:** No cluster or image pipeline; fast `wrangler dev` / `deploy`; instant `workers.dev` URL after auth.
- **More constrained:** Not a Docker host — no arbitrary container image, no shell on the edge, bounded CPU/time.
- **What changed without Docker:** Deployable unit is **script + bindings**, not an image digest; scaling and “region” follow Cloudflare’s anycast edge instead of replica counts you configure.

---
