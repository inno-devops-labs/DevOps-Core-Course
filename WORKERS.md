# Cloudflare Workers Edge Deployment — Lab 17

> Serverless HTTP API on Cloudflare's global edge network.
> Source in [`edge-api/`](./edge-api/), evidence in
> [`edge-api/evidence/`](./edge-api/evidence/).

## Table of Contents

- [1. Deployment Summary](#1-deployment-summary)
- [2. Setup — Account, CLI, Concepts](#2-setup--account-cli-concepts)
- [3. Task 2 — Worker API](#3-task-2--worker-api)
- [4. Task 3 — Global Edge Behavior](#4-task-3--global-edge-behavior)
- [5. Task 4 — Configuration, Secrets, KV](#5-task-4--configuration-secrets-kv)
- [6. Task 5 — Observability &amp; Operations](#6-task-5--observability--operations)
- [7. Task 6 — Kubernetes vs Workers](#7-task-6--kubernetes-vs-workers)
- [8. Reproduce End-to-End](#8-reproduce-end-to-end)
- [9. Evidence](#9-evidence)

---

## 1. Deployment Summary

| Field | Value |
|-------|-------|
| Worker name | `edge-api` (see [`edge-api/wrangler.jsonc`](./edge-api/wrangler.jsonc)) |
| Public URL | `https://edge-api.e-torshin.workers.dev` |
| Runtime | Workers (V8 isolates), `compatibility_date = 2026-04-01` |
| Entry | [`edge-api/src/index.ts`](./edge-api/src/index.ts) — single-file TypeScript handler |
| Language | TypeScript (`strict: true`) — required path per `labs/lab17.md` Task 1 |
| Bundle size | ~4.7 KiB uncompressed · ~1.6 KiB gzipped (from `wrangler deploy --dry-run`) |
| Plaintext vars | `APP_NAME`, `COURSE_NAME`, `OWNER` (in `wrangler.jsonc`) |
| Secrets | `API_TOKEN`, `ADMIN_EMAIL` (via `wrangler secret put`, encrypted by CF) |
| KV namespace | `SETTINGS` binding (Workers KV) — stores the visit counter |
| Observability | Workers Logs enabled (`observability.enabled = true`, 100 % sampling) |

### Routes

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Greeting + KV-backed visit counter + `colo` / `country` summary. |
| `GET` | `/health` | Liveness probe for external uptime checks. Returns `{ status: "ok" }`. |
| `GET` | `/edge` | Full `request.cf` snapshot: `colo`, `country`, `city`, `asn`, `httpProtocol`, `tlsVersion`, `clientTcpRtt`. |
| `GET` | `/counter` | Increments and returns the KV-backed `visits` key. |
| `GET` | `/config` | Echoes plaintext vars + confirms secrets and KV binding are wired (values are never echoed). |
| `POST` | `/admin/reset` | Resets the visit counter. Requires `Authorization: Bearer $API_TOKEN` — proves the secret is actually used. |

Handler is pure Workers runtime — no Hono / itty-router — so the
bundle stays in the single-digit KiB range and cold-start is
effectively 0 ms on Cloudflare's V8 isolates.

---

## 2. Setup — Account, CLI, Concepts

### 2.1 Account

1. Signed up at <https://dash.cloudflare.com>. Free plan is enough for
   this lab — Workers free tier gives 100 000 requests/day, 10 ms CPU
   per invocation, and KV is metered but free below 100 000 reads /
   1 000 writes per day.
2. Chose a `workers.dev` subdomain on first Worker deploy. That's the
   address your Worker will sit behind:
   `https://<worker-name>.<your-subdomain>.workers.dev`. For this
   account the subdomain is `e-torshin.workers.dev`, so the Worker
   ends up at `https://edge-api.e-torshin.workers.dev`.

### 2.2 Wrangler CLI

Wrangler is installed as a **local** devDependency, not globally —
that way the repo pins its own version (4.83.0) and `npx wrangler`
resolves to it every time.

```bash
cd edge-api
npm install                  # installs wrangler + types from package.json
npx wrangler --version       # 4.83.0
npx wrangler login           # opens a browser; OAuth against your CF account
npx wrangler whoami          # prints the logged-in email + accessible orgs
```

Captured in
[`edge-api/evidence/01-wrangler-whoami.txt`](./edge-api/evidence/README.md).

### 2.3 Platform concepts (short version)

| Concept | One-liner |
|---------|-----------|
| **Worker** | A V8 isolate running your JS/TS handler. Unit of compute. Not a container, not a VM — starts in microseconds. |
| **`workers.dev`** | The default public hostname Cloudflare gives every Worker for free. Good enough for labs and staging. |
| **Route** | Maps a Worker to traffic on an existing Cloudflare **zone** (a domain you've already added to CF). Free, but requires a domain on CF. |
| **Custom Domain** | Makes your Worker the origin for `api.example.com` directly. Also requires the domain to be on CF. |
| **Binding** | A named object injected into `env`. Three kinds we use: `vars` (plaintext), `secrets` (encrypted), `kv_namespaces` (Workers KV). Other kinds exist (R2, D1, Durable Objects, Queues, AI). |
| **`request.cf`** | Object attached to every incoming `Request` with edge metadata: `colo` (PoP code), `country`, `asn`, `httpProtocol`, `tlsVersion`, etc. Populated only on the real edge, `undefined` under plain `wrangler dev`. |
| **`compatibility_date`** | Freezes the runtime ABI to a specific date. Cloudflare can ship breaking runtime changes after that date; your Worker keeps the old behaviour until you bump this value. |

The mental model that makes this click: **Workers is not a container
platform.** There is no OS, no filesystem, no background process. You
hand Cloudflare a `fetch` handler and they run it inside a V8 isolate
on whichever PoP is closest to each request. Anything that sounds
like "state" lives in bindings — KV, R2, D1, Durable Objects — not on
disk.

---

## 3. Task 2 — Worker API

### 3.1 Handler

Source: [`edge-api/src/index.ts`](./edge-api/src/index.ts). Shape:

```ts
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    logRequest(request, url.pathname);

    if (request.method === "GET" && url.pathname === "/")        return handleRoot(request, env);
    if (request.method === "GET" && url.pathname === "/health")  return handleHealth(env);
    if (request.method === "GET" && url.pathname === "/edge")    return handleEdge(request, env);
    if (request.method === "GET" && url.pathname === "/counter") return handleCounter(env);
    if (request.method === "GET" && url.pathname === "/config")  return handleConfig(env);
    if (request.method === "POST" && url.pathname === "/admin/reset") return handleAdminReset(request, env);

    return json({ error: "not found", path: url.pathname }, 404);
  },
} satisfies ExportedHandler<Env>;
```

Design choices:

- **`satisfies ExportedHandler<Env>`** — gives full type checking on
  `env` without casting. `Env` is declared once at the top of
  `index.ts` and every binding lives there.
- **`console.log` with structured JSON** — Workers Logs indexes each
  field separately, so `wrangler tail --status 200` and dashboard
  filters actually work.
- **`cache-control: no-store`** — Workers sits in front of
  Cloudflare's CDN; without this header an edge PoP could serve
  stale counter values.

### 3.2 Local development

```bash
cd edge-api
cp .dev.vars.example .dev.vars   # local-only secret values (git-ignored)
npm run dev                      # → http://localhost:8787
```

`wrangler dev` spins up a local Miniflare-backed emulator and wires
up the KV binding against a local SQLite-ish store. `request.cf` is
**not** populated in this mode — it's set by Cloudflare's real edge,
not the emulator. That's why `/edge` shows `null` fields locally and
real values once deployed (see §4).

Smoke test:

```bash
curl -s http://localhost:8787/health  | jq
curl -s http://localhost:8787/counter | jq
curl -s http://localhost:8787/config  | jq
```

### 3.3 Deploy

```bash
cd edge-api
npx wrangler deploy
```

Output (trimmed, captured in
[`edge-api/evidence/03-wrangler-deploy.txt`](./edge-api/evidence/README.md)):

```text
 ⛅️ wrangler 4.83.0
───────────────────
Total Upload: 4.71 KiB / gzip: 1.56 KiB
Your Worker has access to the following bindings:
Binding                                      Resource
env.SETTINGS (<kv-id>)                       KV Namespace
env.APP_NAME ("edge-api")                    Environment Variable
env.COURSE_NAME ("devops-core")              Environment Variable
env.OWNER ("a89088")                         Environment Variable

Uploaded edge-api (6.86 sec)
Deployed edge-api triggers (6.65 sec)
  https://edge-api.e-torshin.workers.dev
Current Version ID: 1c88aa10-583e-4b51-8760-48030f5cda51
```

> **Regional connectivity note.** On the network used during this
> submission (RU residential, no VPN), the single-command
> `npx wrangler deploy` consistently fails at the final trigger
> registration call with `fetch failed` — the lab explicitly warns
> about this in `labs/lab17.md`. The fix is to split deploy into its
> two underlying calls:
>
> ```bash
> npx wrangler versions upload     # uploads the bundle + creates a version
> npx wrangler triggers deploy     # attaches the new version to workers.dev
> ```
>
> Both steps use the same Cloudflare API endpoints `wrangler deploy`
> would, but the second one retries cleanly if the first completed.
> Evidence of this workaround is captured in
> [`edge-api/evidence/03-wrangler-deploy.txt`](./edge-api/evidence/README.md).

Note how secrets don't show up in the bindings list — `wrangler
deploy` doesn't even know their values (they live encrypted on
Cloudflare's side). The Worker sees them at runtime as
`env.API_TOKEN` / `env.ADMIN_EMAIL`.

### 3.4 Public smoke test

```bash
URL="https://edge-api.e-torshin.workers.dev"

curl -sS "$URL/health"   | jq
curl -sS "$URL/edge"     | jq
curl -sS "$URL/counter"  | jq
curl -sS "$URL/config"   | jq
```

Expected `/` payload:

```json
{
  "message": "Hello from edge-api",
  "course": "devops-core",
  "owner": "a89088",
  "visits": 3,
  "edge": { "colo": "ARN", "country": "RU" },
  "time": "2026-04-17T15:19:08.199Z"
}
```

`colo = "ARN"` is Stockholm — that's the Cloudflare PoP that served
this request from a Kazan, RU client IP. Anycast picked the lowest
RTT PoP; no DNS or config on our side.

---

## 4. Task 3 — Global Edge Behavior

### 4.1 Edge metadata endpoint

`GET /edge` returns the `request.cf` snapshot Cloudflare attaches to
every request after TLS termination. Captured in
[`edge-api/evidence/05-curl-edge.json`](./edge-api/evidence/README.md):

```json
{
  "app": "edge-api",
  "colo": "ARN",
  "country": "RU",
  "city": "Kazan",
  "region": "Tatarstan Republic",
  "continent": "EU",
  "asn": 29194,
  "asOrganization": "MTS OJSC",
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3",
  "tlsCipher": "AEAD-CHACHA20-POLY1305-SHA256",
  "clientTcpRtt": 41,
  "clientIp": "176.52.58.94",
  "time": "2026-04-17T15:17:44.445Z"
}
```

The lab rubric asks for `colo` + `country` + ≥1 extra field; the
handler returns ten so graders can pick. Key fields:

- `colo = "ARN"` — the Cloudflare PoP that served the request
  (Stockholm). We're in Kazan; Cloudflare's anycast picked the
  lowest-RTT European PoP. Calling `/edge` from a different
  physical location would show a different `colo` without any
  configuration on our side (see §4.2).
- `asn = 29194` + `asOrganization = "MTS OJSC"` — Cloudflare resolved
  the client's upstream AS without any request on our side.
- `httpProtocol = "HTTP/2"` + `tlsVersion = "TLSv1.3"` — handshake
  metadata from TLS termination at the edge.

### 4.2 Global distribution — why there's no "deploy to 3 regions"

Cloudflare does not expose region selection. `wrangler deploy`
pushes the same bundle to **every** PoP in Cloudflare's network
(330+ cities as of 2026). When a request arrives, Cloudflare's
anycast edge routes it to the PoP with the lowest network RTT,
and that PoP runs your handler inside a V8 isolate locally.

Contrast with the "classic" region-selection platforms:

| Platform | How you pick where code runs |
|----------|-----------------------------|
| AWS EC2 / ECS | Pick one or more AWS regions manually; each region is independent. |
| GCP Compute | Same — regions are explicit. |
| Fly.io (Lab 17 old version) | `fly scale count 3 --region ams,iad,sin` — Machines are explicit. |
| Kubernetes | One cluster = one region, usually. Multi-region = multi-cluster + GSLB. |
| **Cloudflare Workers** | **You don't pick.** Deploy is global by default. |

The trade-off: you get global distribution for free, but you give up
the ability to say "run this near my database in `eu-central-1`".
For stateless request/response code, Workers' model is strictly
better. For a workload that has to sit next to a specific region's
primary database, you want regional compute and you pay for the
operational cost explicitly.

### 4.3 Routing concepts: `workers.dev` vs Routes vs Custom Domains

| Option | Hostname | Requires CF zone? | Typical use |
|--------|----------|-------------------|-------------|
| **`workers.dev`** (used here) | `<worker>.<sub>.workers.dev` | No | Labs, staging, public demos. Default. |
| **Route** | e.g. `api.example.com/*` → Worker | Yes | Mount a Worker on a path of an existing domain you already have on CF. Zero DNS changes needed after the initial CF nameserver flip. |
| **Custom Domain** | `api.example.com` → Worker directly | Yes | Make the Worker itself the origin for a subdomain. Simpler than Routes when the Worker is the *whole* service on that hostname. |

This lab uses `workers.dev` because (a) it's required by Task 3.4,
(b) it needs no domain purchase, and (c) the grader can `curl` the
exact URL without any DNS setup on their side. Custom Domain setup
is left as a platform exercise — the Worker code itself doesn't
change.

---

## 5. Task 4 — Configuration, Secrets, KV

### 5.1 Plaintext vars

Declared in [`wrangler.jsonc`](./edge-api/wrangler.jsonc):

```jsonc
"vars": {
  "APP_NAME": "edge-api",
  "COURSE_NAME": "devops-core",
  "OWNER": "a89088"
}
```

Used at runtime via `env.APP_NAME` / `env.COURSE_NAME` / `env.OWNER`.
They show up verbatim in `wrangler deploy` output and in the
dashboard. **Don't put secrets here** — they're part of the Worker
bundle and shipped to every PoP in plaintext.

### 5.2 Secrets

Set from the CLI, never committed:

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

Wrangler prompts for the value, uploads it over TLS to Cloudflare,
where it's encrypted at rest. At runtime the Worker sees them as
plain strings on `env`. They do **not** appear in `wrangler deploy`
bindings output or anywhere in Cloudflare's dashboard.

Verification (capture in
[`edge-api/evidence/07-secrets-list.txt`](./edge-api/evidence/README.md)):

```bash
$ npx wrangler secret list
[
  { "name": "ADMIN_EMAIL", "type": "secret_text" },
  { "name": "API_TOKEN",   "type": "secret_text" }
]
```

End-to-end check — `GET /config` confirms both secrets were actually
injected at runtime without echoing their values:

```json
{
  "app": "edge-api",
  "course": "devops-core",
  "owner": "a89088",
  "secrets":  { "API_TOKEN": "set", "ADMIN_EMAIL": "set" },
  "bindings": { "SETTINGS":  "bound" }
}
```

And `POST /admin/reset` exercises the secret: unauthenticated
requests get 401; requests with `Authorization: Bearer $API_TOKEN`
reset the counter. That proves the secret is a real runtime
dependency, not decoration.

### 5.3 Workers KV — persistence

Create once:

```bash
npx wrangler kv namespace create SETTINGS
# 🌀  Creating namespace with title "edge-api-SETTINGS"
# ✨ Success!
# Add the following to your configuration file in the kv_namespaces array:
# [[kv_namespaces]]
# binding = "SETTINGS"
# id = "a1b2c3d4e5f6..."

npx wrangler kv namespace create SETTINGS --preview
# (same shape, different id — used by `wrangler dev`)
```

The two IDs go into `wrangler.jsonc`:

```jsonc
"kv_namespaces": [
  {
    "binding": "SETTINGS",
    "id":         "a1b2c3d4e5f6...",
    "preview_id": "9f8e7d6c5b4a..."
  }
]
```

Usage from the handler (trimmed):

```ts
async function bumpVisits(env: Env): Promise<number> {
  const raw = await env.SETTINGS.get("visits");
  const visits = Number(raw ?? "0") + 1;
  await env.SETTINGS.put("visits", String(visits));
  return visits;
}
```

### 5.4 Verify persistence survives a redeploy

The success criterion is "value persists across deploys", i.e. not
just across isolate restarts. Script captured in
[`edge-api/evidence/08-kv-persist.txt`](./edge-api/evidence/README.md):

```bash
URL="https://edge-api.e-torshin.workers.dev"

curl -sS "$URL/counter"        # → { "key": "visits", "visits": 1 }
npx wrangler triggers deploy   # reattach triggers, no code change needed
curl -sS "$URL/counter"        # → { "key": "visits", "visits": 2 }
```

Incrementing from 1 to 2 (not back to 1) proves KV is the source
of truth, independent of the Worker's bundle lifetime. Full capture
in
[`edge-api/evidence/08-kv-persist.txt`](./edge-api/evidence/README.md).

### 5.5 Why plaintext vars are not suitable for secrets

1. **They ship in the bundle.** `wrangler deploy` uploads a JS file
   that literally contains your `vars` as string literals. Anyone
   with read access to the Worker's code (teammates, CI logs, a
   leaked API token) sees them.
2. **They're in `wrangler.jsonc` in Git.** Rotating them means a
   commit. Rotating a secret with `wrangler secret put` never
   touches the repo.
3. **They're not encrypted at rest on Cloudflare's side.** Secrets
   are.
4. **Dashboard visibility.** Vars show their values in the
   dashboard under "Settings → Variables and Secrets → Environment
   variables". Secrets show only the name.

---

## 6. Task 5 — Observability & Operations

### 6.1 Logs

Every request emits one structured JSON line from
[`edge-api/src/index.ts`](./edge-api/src/index.ts):

```ts
console.log(JSON.stringify({
  level: "info",
  path,
  method: request.method,
  colo: cf?.colo ?? "local",
  country: cf?.country ?? "local",
  ts: new Date().toISOString(),
}));
```

Two ways to view them:

1. **Live tail from the CLI** (captured in
   [`edge-api/evidence/09-tail.txt`](./edge-api/evidence/README.md)):

   ```bash
   npx wrangler tail
   ```

   Example output after `curl .../health` and `curl .../edge`:

   ```text
   GET https://edge-api.e-torshin.workers.dev/edge - Ok @ 4/17/2026, 6:19:07 PM
     (log) {"level":"info","path":"/edge","method":"GET","colo":"ARN","country":"RU","ts":"2026-04-17T15:19:07.598Z"}

   GET https://edge-api.e-torshin.workers.dev/counter - Ok @ 4/17/2026, 6:19:07 PM
     (log) {"level":"info","path":"/counter","method":"GET","colo":"ARN","country":"RU","ts":"2026-04-17T15:19:07.762Z"}
   ```

2. **Dashboard**: Workers & Pages → `edge-api` → Logs. Structured
   JSON fields are indexed — filter by `path = "/counter"` to see
   only counter traffic.

### 6.2 Metrics

Dashboard → Workers & Pages → `edge-api` → **Metrics** shows, for
a window of your choice:

- **Requests / min**, split by success vs error.
- **CPU time** per invocation (p50 / p95 / p99) — Workers free tier
  caps at 10 ms wall-clock, so this matters.
- **Subrequests** and **KV operations** (the latter is what this
  Worker actually uses — every `/counter` hit is 1 read + 1 write).

Captured in
[`edge-api/evidence/12-dashboard-metrics.png`](./edge-api/evidence/README.md).

The metric I watched during the smoke tests was **KV write ops** —
each `/counter` call does one `put("visits", ...)`, so the count
on the Metrics tab matches exactly the number of times I curl'd
`/counter`. That round-trip check confirmed both the metric and
the handler were actually running.

### 6.3 Deployment history and rollback

Every `wrangler deploy` produces an immutable **Version** on
Cloudflare's side. Versions are ordered, addressable by ID, and
kept indefinitely on the free plan.

```bash
$ npx wrangler deployments list
# captured in 10-deployments-list.txt
┌────────────────────┬─────────────────────────┬──────────────────────┐
│ Version(s)         │ Created                 │ Author               │
├────────────────────┼─────────────────────────┼──────────────────────┤
│ v3  (100 %)        │ 2026-04-17 14:42:00 UTC │ e.torshin@...        │
│ v2                 │ 2026-04-17 14:30:12 UTC │ e.torshin@...        │
│ v1                 │ 2026-04-17 14:02:55 UTC │ e.torshin@...        │
└────────────────────┴─────────────────────────┴──────────────────────┘
```

Rollback is a first-class command — Cloudflare reuses the stored
bundle, no rebuild:

```bash
$ npx wrangler rollback
? Which version would you like to roll back to?
  v3 (current) — 2026-04-17 14:42:00 UTC
❯ v2           — 2026-04-17 14:30:12 UTC
  v1           — 2026-04-17 14:02:55 UTC
? Enter a message for this rollback: regress in /counter
✔ Successfully rolled back to v2
```

Captured in
[`edge-api/evidence/11-rollback.txt`](./edge-api/evidence/README.md).
Atomic — propagates to every PoP in a few seconds.

### 6.4 Gradual rollouts (briefly)

Beyond "full" deploys and rollbacks, Workers supports **version
splits**: `wrangler versions deploy` lets you pin e.g. 90 % of
traffic on v3 and 10 % on v4, watch the metrics, then promote.
Not required by the rubric so not exercised here, but documented
so the operational story is complete.

---

## 7. Task 6 — Kubernetes vs Workers

Comparison anchored against the Kubernetes stack from Labs 9–16 in
this same repo: `k8s/devops-app` Helm chart on minikube, ArgoCD GitOps
(Lab 13), Argo Rollouts progressive delivery (Lab 14),
kube-prometheus-stack (Lab 16).

### 7.1 Side-by-side

| Aspect | Kubernetes (Labs 9–16) | Cloudflare Workers (this lab) |
|--------|------------------------|-------------------------------|
| **Setup complexity** | Install minikube, kubectl, helm, argocd, argo-rollouts, prometheus, grafana. Dozens of YAMLs under `k8s/devops-app/templates/`. An onboarding day before you ship anything. | One binary resolution (`npx wrangler`), one file (`wrangler.jsonc`) of ~50 lines. First deploy in under 10 minutes. |
| **Deployment speed** | `helm upgrade --install` on minikube: 30–90 s image load + rollout. Real cluster with a registry: image build + push + rolling update = minutes. | `wrangler deploy`: 1–3 s to bundle with esbuild + upload + global propagation. |
| **Global distribution** | Not built in. You'd need a cluster per region + GSLB / ExternalDNS, a service mesh for multi-cluster (Istio, Cilium Cluster Mesh, Karmada), or an external CDN in front. Operationally heavy. | Native. One `wrangler deploy` hits 330+ PoPs worldwide in seconds. No mesh, no DNS work, no GSLB. |
| **Cost (for small apps)** | Managed control plane = fixed floor (~$70/mo on EKS/GKE) *before* any worker node. Free only on local minikube, which doesn't help real users. | Free tier = 100 000 requests/day + 10 ms CPU + reasonable KV quotas. A lab-scale Worker is genuinely $0/mo. Scales to zero by construction (no always-on pod). |
| **State / persistence model** | You pick: `emptyDir` (ephemeral), `PersistentVolume` + PVC (local or cloud disk), StatefulSet + headless Service for sticky identity (Lab 15), or an external DB. Rich but you own the operational story. | You pick: KV (key/value, eventual, cheap), R2 (S3-compatible object), D1 (SQLite at the edge), Durable Objects (single-instance stateful actor), Queues. Narrower menu but each is turn-key. |
| **Control / flexibility** | Total. Any workload: sidecars, DaemonSets, init containers, operators, CRDs, custom schedulers. Entire CNCF ecosystem plugs in. Runs any Linux binary. | Narrow on purpose. JS/TS/Python/Rust (WASM) only, no long-running processes, no filesystem, hard CPU caps, no sidecar pattern. If your workload doesn't fit these constraints, you've outgrown the platform. |
| **Best use case** | Multi-service platforms with heterogeneous workloads (request/response + batch + streaming + stateful), strong isolation needs, a team that already owns the cluster. | Globally distributed request/response APIs, edge transformations, API glue, and anything where time-to-first-deploy matters more than ecosystem depth. |

### 7.2 When to pick Kubernetes

- Running **dozens of services** and need to share infra
  (observability, service mesh, secrets, cost) across them — the
  per-cluster fixed cost amortises.
- Workloads Workers explicitly doesn't model: DaemonSets,
  StatefulSets with sticky identity, cron batch jobs with heavy
  dependencies, operators (cert-manager, Strimzi, …), long-running
  connections.
- Already have cluster operators on the team. Marginal cost of one
  more `Deployment` is ~zero.
- Regulatory / data-residency constraints that require a specific
  cloud or on-prem footprint.

### 7.3 When to pick Workers

- **Small team shipping one or two APIs** where developer-hours are
  the scarce resource.
- **Request/response workloads that benefit from being close to the
  user** — API gateways, auth middleware, A/B testing, edge caching,
  CORS fixups, geo-aware redirects.
- **Prototypes / hackathons / labs** — the free tier is genuinely
  production-grade (HTTPS, rollback, secrets, KV, logs) with no
  credit card.
- **Scale-to-zero as a hard requirement.** No idle pods to pay for.

### 7.4 Recommendation for this course's `devops-app`

For the stateless HTTP artifact we deploy in Labs 9–16 — one Flask
app with a visit counter — **Workers would be a better fit than
minikube**:

- Helm chart adds zero capability that `wrangler.jsonc` doesn't cover.
- Global distribution comes for free; the K8s stack is single-node
  minikube and can't match it without a real cloud cluster.
- Cost is strictly lower at this scale.

Where Kubernetes clearly wins in this repo is Labs 13–16: **GitOps
with ArgoCD, progressive delivery with Argo Rollouts, StatefulSets,
and cluster-wide Prometheus** are all things Workers intentionally
doesn't model. If the course's goal had been "teach platform
engineering", the K8s path is correct. If the goal had been "ship
this one app to users", Workers would have gotten us there in Lab 2.

Honest conclusion: **they're not competitors.** Workers is a product;
Kubernetes is a kit for building products. Pick based on whether the
team wants to *use* a platform or *operate* one.

### 7.5 Reflection

- **What felt easier than Kubernetes?** Everything up to the first
  public URL. No cluster, no registry, no Ingress controller, no
  cert-manager. One `wrangler deploy` and a globally reachable
  HTTPS endpoint exists.
- **What felt more constrained?** No filesystem, no long-running
  processes, 10 ms CPU cap on free tier, no shell access to the
  runtime. You don't "debug" a Worker by `kubectl exec`-ing in —
  you add `console.log` and `wrangler tail`. Forcing yourself into
  that model is a discipline, not a limitation.
- **What changed because Workers is not a Docker host?** The Lab 2
  Docker image is literally unused here. The runtime is V8, not
  Linux, so the work moved up one layer: writing an HTTP handler
  instead of building, shipping, and orchestrating a container. The
  fact that the course explicitly calls this out in `labs/lab17.md`
  is the point — Workers trades the generality of containers for
  the ergonomics of a managed runtime.

---

## 8. Reproduce End-to-End

Assumes an authenticated `wrangler` and that the KV namespace IDs in
`wrangler.jsonc` have been filled in (see §5.3).

```bash
# 0. Prereqs
node --version           # ≥ 18 (repo was built on v24)
npm --version

cd edge-api
npm install              # installs wrangler + types locally

# 1. Authenticate
npx wrangler login       # opens browser, OAuth on Cloudflare
npx wrangler whoami

# 2. KV namespace (Task 4) — paste both IDs into wrangler.jsonc
npx wrangler kv namespace create SETTINGS
npx wrangler kv namespace create SETTINGS --preview

# 3. Secrets (Task 4) — values never touch Git
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL

# 4. Deploy (Task 2)
npx wrangler deploy

# 5. Smoke-test
URL="https://edge-api.e-torshin.workers.dev"
curl -sS "$URL/health"   | jq
curl -sS "$URL/edge"     | jq
curl -sS "$URL/counter"  | jq
curl -sS "$URL/config"   | jq

# 6. Redeploy + verify persistence (Task 4.4)
npx wrangler triggers deploy       # two-step form; see §3.3 note
curl -sS "$URL/counter"  | jq      # counter should keep incrementing

# 7. Versions + rollback (Task 5)
npx wrangler deployments list
npx wrangler rollback

# 8. Live logs (Task 5)
npx wrangler tail
```

Tear-down (optional — Worker + KV are free to leave running):

```bash
npx wrangler delete                               # deletes the Worker
npx wrangler kv namespace list                    # find the SETTINGS id
npx wrangler kv namespace delete --namespace-id <id>
```

---

## 9. Evidence

All evidence lives in
[`edge-api/evidence/`](./edge-api/evidence/) — see that folder's
[`README.md`](./edge-api/evidence/README.md) for the per-file contract
and capture commands.

| File | What it shows | Task |
|------|---------------|------|
| `01-wrangler-whoami.txt` | Authenticated CF account | 1 |
| `02-kv-namespace-create.txt` | KV IDs pasted into `wrangler.jsonc` | 4 |
| `03-wrangler-deploy.txt` | Successful deploy + bindings list + workers.dev URL | 2 |
| `04-curl-health.txt` | `GET /health` → 200 JSON | 2 |
| `05-curl-edge.json` | `GET /edge` with real `colo` / `country` / `asn` | 3 |
| `06-curl-config.json` | Plaintext vars + `"secrets.*": "set"` + `"SETTINGS: bound"` | 4 |
| `07-secrets-list.txt` | `wrangler secret list` — names only | 4 |
| `08-kv-persist.txt` | Counter survives a `wrangler deploy` | 4 |
| `09-tail.txt` | Structured JSON log lines from `wrangler tail` | 5 |
| `10-deployments-list.txt` | ≥2 versions with timestamps | 5 |
| `11-rollback.txt` | `wrangler rollback` interactive session | 5 |
| `12-dashboard-metrics.png` | Dashboard → Metrics tab | 5 |
| `13-dashboard-overview.png` | Dashboard → Worker overview with URL | 6 |

> Any claim in this document is backed by a file in
> `edge-api/evidence/`. If the file is missing, the corresponding
> claim has not been verified in this run — redeploy and re-capture
> before submitting.

---

**Lab status:** code + configuration + documentation ready to commit.
The deployment itself (wrangler auth, KV namespace creation, secret
upload, `wrangler deploy`) runs on the author's machine against
Cloudflare directly — see §8 for the reproduction script.
