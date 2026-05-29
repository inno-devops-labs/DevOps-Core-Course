# Lab 17 — Cloudflare Workers Edge Deployment

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Edge%20Computing-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![type](https://img.shields.io/badge/type-Exam%20Alternative-purple)

> **Goal:** Build a serverless HTTP API on Cloudflare's global edge — a V8 isolate, not a container — and back it with your Lab 9 Kubernetes measurements in a real comparison.
> **Deliverable:** A PR from `lab17` with `edge-api/` (the Worker project) and `docs/LAB17.md` (the comparison + evidence).

## Overview

Cloudflare Workers runs your code in a **V8 isolate** — a sandboxed JS heap inside an already-running `workerd` process at 330+ points of presence. Cold start is **<5 ms**, the memory floor is ~3 MB per isolate, and there is no region to pick: every deploy is global. That is the opposite end of the abstraction spectrum from the Kubernetes you built across Labs 9–16.

In this lab you will practice:
- Scaffolding a Worker with **Wrangler 4.95+** (4.x is **local-first** by default; `--remote` is opt-in)
- Writing the `export default { async fetch(...) }` handler shape from the V8 runtime
- Wiring edge-attached state with **Workers KV** + Wrangler secrets
- Reading edge request metadata (`request.cf.colo`) to prove the PoP routing model
- Producing an **honest, measured comparison** of Workers vs your Lab 9 K8s deployment

> ⚠️ **Scope:** this lab does **not** ship your Lab 2 Docker image. Workers has no `FROM`, no ingress, no HPA, no filesystem. You will build a Workers-native API that preserves the same operational concerns (routes, health, config, state, logs, deploys) in the edge model — and write up where that re-shapes the problem.

> ⚠️ **This is a bonus / Exam Alternative lab.** Complete both Lab 17 (12 pts) and Lab 18 (12 pts) to the required bar to replace the final exam.

---

## Exam Alternative Requirements

| Requirement | Details |
|---|---|
| **Deadline** | 1 week before the exam date |
| **Minimum Score** | **10/12** on each of Lab 17 and Lab 18 |
| **Must Complete** | Both Lab 17 **and** Lab 18 |
| **Total Points** | Together they form the **exam replacement** option |

> Taken on its own, Lab 17 is a **bonus** lab: **10 pts** of main tasks + a **2 pt** bonus task = **12 pts max**.

---

## Project State

**You should have from previous labs:**
- **Lab 9** — your K8s Deployment + Service running on k3d, with the same HTTP service you've been growing since Lab 1. You'll re-use its cold-start, latency, and resource numbers in Task 3.

**This lab adds:**
- `edge-api/` — a Cloudflare Worker (one `src/index.js`, one `wrangler.toml`, one KV namespace)
- `docs/LAB17.md` — your submission report including the K8s-vs-Workers comparison

> **Regional connectivity note:** In some countries and networks (including parts of Russia), Cloudflare services may be partially restricted. If `npx wrangler whoami` or `npx wrangler deploy` fail with vague network errors, the problem may be your network path. If you use a VPN, prefer **full-tunnel** / global-routing mode — split-tunnel setups can let Node.js traffic bypass the VPN and hit the restricted network.

> **No Cloudflare account?** You can complete every task except the live `workers.dev` deploy and `request.cf` capture using `wrangler dev --local` (`workerd` runs the same V8 isolate runtime locally). See the **Documented-gap** sub-section under Task 1.6 for the substitute proof. The bonus task and full marks on Task 3 still require a real deploy.

---

## Setup

You need:

```bash
node --version           # 18+
npm --version
npx wrangler --version   # 4.95.0 or newer (4.x is local-first)
```

If Wrangler isn't installed yet, you'll install it via the C3 scaffolder in Task 1.

---

## Task 1 — Scaffold, Build & Deploy a Worker API (4 pts)

### 1.1 — Scaffold the project

Use C3 (`create-cloudflare`) with the **Hello World / Worker only** template:

```bash
npm create cloudflare@latest -- edge-api
cd edge-api
```

When prompted, pick: *Hello World example* → *Worker only* → **JavaScript** (you may use TypeScript if you prefer; the skeleton below is JS) → Git: **Yes** → Deploy now: **No**.

Then:

```bash
npx wrangler --version   # confirm 4.95 or newer
```

> Why 4.95+? Wrangler 4.x switched `wrangler dev` to **local-first** — it runs your Worker in `workerd` on your machine. The `--remote` flag is now opt-in. If you're on a stale 3.x, `dev` hits Cloudflare's preview infra, which behaves differently (and costs requests).

### 1.2 — Configure `wrangler.toml`

The C3 scaffolder generates a `wrangler.jsonc`. Either keep that or rename to `wrangler.toml` — both work; this lab uses TOML for brevity. Open it and fill in the values yourself:

```toml
# wrangler.toml — YOUR TASK: fill every value
name = "___"                    # YOUR TASK: pick a worker name (lowercase, hyphens, your-handle-ish)
main = "___"                    # YOUR TASK: path to your entry file (e.g. src/index.js)
compatibility_date = "___"      # YOUR TASK: ISO date — pin runtime behavior; pick today (YYYY-MM-DD)

# Plaintext vars (Task 2 will add real ones)
[vars]
APP_NAME = "edge-api"
```

> **Why `compatibility_date`?** It pins the `workerd` runtime semantics so Cloudflare can ship new defaults without breaking your Worker. Picking today's date is fine; never leave it blank.

### 1.3 — Write the `fetch` handler

Open `src/index.js`. The C3 scaffold gives you a "Hello World" — **delete it**. The Worker entry point is a single object exported as `default`, with one async `fetch(request, env, ctx)` method. That's the entire shape:

```javascript
// src/index.js
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // YOUR TASK: route on url.pathname for "/", "/health", "/echo"
    // YOUR TASK: GET /         → Response.json with service info
    //            keys (mirror Lab 1 shape): { service, version, framework, runtime, edge: { colo }, path }
    // YOUR TASK: GET /health   → Response.json({ status: ___, edge: true }) with HTTP 200
    // YOUR TASK: /echo
    //            POST → echo the request body back (same Content-Type)
    //            GET  → 405 Method Not Allowed, JSON body { error: ___, allow: ___ }
    // YOUR TASK: anything else → 404 with JSON body { error: ___, path: url.pathname }

    return ___;
  }
};
```

Requirements:

- **`GET /`** returns five top-level keys minimum: `service`, `version`, `framework` (`"cloudflare-workers"`), `runtime` (`"v8-isolate"`), `edge.colo` (read from `request.cf?.colo` — see note below), and `path`. Keep it shaped like Lab 1's `/` JSON so the contrast is fair.
- **`GET /health`** returns `{ status: "ok", edge: true }` with HTTP 200. This is what `wrangler tail` will help you observe in Task 3.
- **`POST /echo`** reads the request body (`await request.text()` or `await request.json()`) and returns it. `GET /echo` returns **405** with `Allow: POST` semantics in the JSON.
- **Anything else** returns **404** with a JSON body (never HTML — same lesson as Lab 1).

> **`request.cf?.colo`** is populated by Cloudflare at the real edge. In `wrangler dev --local` it's `undefined` or a stub (`"TBS"`). That's expected; your `/` handler should use optional chaining so it doesn't throw.

> **`Response.json(obj, init?)`** is the modern way to return JSON from a Worker — sets `Content-Type: application/json` for you. Available since `compatibility_date: 2022-01-31`. If you set an older date you'd have to do `new Response(JSON.stringify(obj), { headers: { "content-type": "application/json" } })` by hand — another reason to pin a recent date in 1.2.

### 1.4 — Run locally on `workerd`

```bash
npx wrangler dev
```

Wrangler boots a `workerd` process on `http://localhost:8787`. This is the **same** V8-isolate runtime Cloudflare runs at the edge — local dev is faithful to production behavior (modulo `request.cf` and global routing).

`YOUR TASK`: hit every route with `curl` and capture the JSON. Suggested checks:

- `curl -s http://localhost:8787/ | jq .`
- `curl -s http://localhost:8787/health | jq .`
- `curl -s -X POST -H 'content-type: application/json' -d '{"ping":42}' http://localhost:8787/echo | jq .`
- `curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8787/echo` (GET → expect `HTTP 405`)
- `curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8787/nope` (expect `HTTP 404`)

### 1.5 — Deploy globally

```bash
npx wrangler login         # OAuth in browser; opens a localhost callback
npx wrangler whoami        # confirms account + lists your workers.dev subdomain
npx wrangler deploy
```

> ⚠️ **Headless / remote-VM gotcha:** `wrangler login` opens a browser locally and listens on `127.0.0.1:8976` for the OAuth callback. If you're SSH'd into a remote VM with no local browser, the callback never reaches your browser. Two options: (a) `ssh -L 8976:localhost:8976 <user@host>` to port-forward the OAuth callback to your laptop, or (b) export `CLOUDFLARE_API_TOKEN=<token>` from a token you create in the dashboard (Account → API Tokens → "Edit Cloudflare Workers" template). Document the path you took in §1.6.

The output prints `https://<worker-name>.<your-subdomain>.workers.dev`. Hit it with `curl` and confirm the same JSON — except `edge.colo` is now a **real** PoP code (`"FRA"`, `"WAW"`, `"SVO"`, ...).

### 1.6 — Proof of work

**Paste into `docs/LAB17.md`:**

- `npx wrangler --version` output (must be 4.95+)
- All five `curl` captures from 1.4 against `localhost:8787` (with the **exact commands** you ran)
- Either:
  - **(a)** `curl` capture of `GET /` against your deployed `workers.dev` URL showing a **real** `edge.colo`, *or*
  - **(b)** **Documented-gap** sub-section: explain that you have no CF account (or are on a network where deploy is blocked), then paste the **local** `GET /` capture and write 2–3 sentences on what would be different at the real edge (`colo` populated, latency under 50 ms in your region, anycast routing).

---

## Task 2 — Config, Secrets & Edge State (3 pts)

### 2.1 — Why this matters

Your Worker now responds. The next test is whether you can give it **configuration** (vars), **credentials** (secrets), and **state** (KV) without ever putting them in Git. This is the same separation-of-concerns problem you solved in Labs 1 (env vars), 11 (OpenBao secrets), and 12 (ConfigMaps + PVCs) — the primitives are just edge-shaped.

### 2.2 — Plaintext variable

You already added `APP_NAME` to `wrangler.toml` in 1.2. `YOUR TASK`: read it inside the Worker (`env.APP_NAME`) and surface it in your `GET /` `service` field. In one sentence in `docs/LAB17.md`, say why vars are **unsuitable for secrets** (hint: they're in the dashboard + Git + readable by any collaborator).

### 2.3 — Wrangler secrets

Create **two** secrets. Wrangler prompts you for the value — it never lands in your repo:

```bash
npx wrangler secret put ___        # YOUR TASK: name your first secret
npx wrangler secret put ___        # YOUR TASK: name your second secret
npx wrangler secret list           # names only, no values
```

Then read them inside the Worker. The bindings appear on `env`:

```javascript
// YOUR TASK: in your fetch handler, read the secret you put above
const token = env.___;             // YOUR TASK: must match the name in `wrangler secret put`
```

Surface one of them in a **gated** route — for example, `GET /admin` returns 401 unless `request.headers.get("authorization") === \`Bearer ${env.YOUR_SECRET}\``. The point is to prove the secret round-trips from `wrangler secret put` → `env` → request handling.

> **Local dev + secrets:** `wrangler dev` reads local-only overrides from `.dev.vars` (a gitignored file shaped like `.env`). For the real deploy, only `wrangler secret put` counts.

### 2.4 — Workers KV (mandatory)

KV is Workers' eventually-consistent key/value store — the right primitive for flags, counters, and small config blobs. Two-step setup: create the namespace, then bind it.

```bash
npx wrangler kv namespace create ___      # YOUR TASK: pick a binding name (e.g. SETTINGS)
```

The command prints a config snippet. Copy the **id** it gives you into `wrangler.toml`:

```toml
[[kv_namespaces]]
binding = "___"     # YOUR TASK: same binding name you used above — this is what env.<binding> exposes
id      = "___"     # YOUR TASK: the namespace id Wrangler just printed (a 32-char hex string)
```

Then write a `/counter` route that increments a KV-backed visit counter:

```javascript
// YOUR TASK: inside fetch, handle url.pathname === "/counter"
// 1. read the current value with env.<binding>.get("visits") (returns string or null)
// 2. compute the next integer
// 3. write it back with env.<binding>.put("visits", String(n))
// 4. return Response.json({ visits: n })
```

Round-trip from the CLI to convince yourself the namespace is real:

```bash
npx wrangler kv key put --binding=___ "visits" "0"        # YOUR TASK: binding name
npx wrangler kv key get --binding=___ "visits"            # YOUR TASK: same binding
```

> **D1, R2, Durable Objects** all live on the same `env.<binding>` model:
> - **D1** — SQLite per region, replicated. Use when you need joins.
> - **R2** — S3-compatible blob storage, **no egress fees**. Use for assets/backups.
> - **Durable Objects** — strongly-consistent stateful actors. Use for chat rooms, leaderboards, rate-limiters.
> KV is the right pick here; the Bonus Task lets you swap in one of the others.

### 2.5 — Proof of work

**Paste into `docs/LAB17.md`:**

- `npx wrangler secret list` output showing your two secret **names** (values must not appear)
- A `curl` proving the gated route from 2.3 — one call without the header (401), one with (200)
- `npx wrangler kv key put` / `kv key get` round-trip from 2.4 (illustrative IDs are fine; your IDs will differ)
- A `curl http://localhost:8787/counter` (or your deployed URL) hit **three times** — the third response must show `visits: 3` *and* must continue, not reset, across a redeploy if you deployed
- The one-sentence reason vars are unsuitable for secrets

---

## Task 3 — Observability, Ops & K8s Comparison (3 pts)

This is the lecture-16 payoff. Workers and K8s solve the same problem (run my HTTP code in production); they pay very different prices.

### 3.1 — Live logs

Add at least one `console.log()` call in your `fetch` handler — log the path and the (possibly undefined) colo:

```javascript
// YOUR TASK: add console.log with at least the path and request.cf?.colo
console.log(___);
```

Then in another terminal:

```bash
npx wrangler tail
```

Hit any route from a third shell. The log line streams from the edge in near real-time.

`YOUR TASK`: capture **one** `wrangler tail` line — paste the literal log entry (timestamps and all) into `docs/LAB17.md`.

### 3.2 — Versions and rollback

Deploy at least **two** versions of your Worker. Trivial change between them is fine (bump the `version` field in `GET /`). Then list and roll back:

```bash
npx wrangler deployments list      # YOUR TASK: capture this — version IDs + timestamps
npx wrangler rollback              # YOUR TASK: capture this — confirms the rollback
```

If you have no CF account, document this as a gap: explain what each command would print (Wrangler shows a numbered list of versions with author + timestamp; `rollback` prompts confirmation then restores the previous version atomically).

### 3.3 — The K8s vs Workers table (the whole point)

Pull up your **Lab 9** notes: cold start of a fresh pod, request latency from your laptop to the k3d Service, the resources you reserved per pod. If you've forgotten, re-run `kubectl get pods -w` against a fresh Deployment and `time curl ...` once it's Ready. Then fill the table **with your own measurements** — not the lecture's defaults:

`YOUR TASK`: fill every cell of this table in `docs/LAB17.md`. Cite where each number came from.

| Aspect | Kubernetes (Lab 9, your numbers) | Cloudflare Workers (this lab, your numbers) |
|---|---|---|
| Cold start (first request after scale-from-zero) | ___ s (`kubectl get pods -w` from `Pending` → `Ready` + first `200`) | ___ ms (`time curl` against fresh deploy) |
| Memory floor per instance | ___ Mi (your pod `resources.requests.memory`) | ~3 MB (V8 isolate, documented) |
| Geographic distribution | ___ (your single k3d node — what region/laptop) | 330+ PoPs, all of them automatically |
| Cost per 1M requests at idle | ___ ($/mo at 0 traffic — your node bill if rented; $0 on k3d, but say what a managed equivalent would cost) | **Free tier:** 100k req/day × 30 = ~3M/mo at $0. **Paid ($5/mo):** 10M req + 50 ms CPU |
| State primitive used | ___ (e.g. PVC + local-path from Lab 12) | Workers KV (this lab) |
| Long-running task support | yes — any process | 30 s wall-clock max (paid), CPU 10 ms (free) / 50 ms (paid, burstable to 5 min) |
| Best use case | ___ (your one-line take) | ___ (your one-line take) |

> **The point:** Workers wins on cold start and price floor for spiky, latency-sensitive APIs. K8s wins on long-running, stateful, native, multi-service workloads. The numbers from your own labs are what make the comparison honest.

### 3.4 — Reflection (3 sentences, in `docs/LAB17.md`)

`YOUR TASK`: answer in your own words —

1. What was **easier** in Workers than in your K8s setup from Lab 9?
2. What felt **more constrained**? (V8 isolate has no `fs`, no `Buffer` by default, no native binaries, 10 ms CPU on free tier.)
3. What changed because Workers is **not a Docker host**? (Think: no `Dockerfile`, no scan, no ingress, no HPA — but also no choice about base image, no Lab 2 multi-stage trick to fall back on.)

### 3.5 — Proof of work

**Paste into `docs/LAB17.md`:**

- The `wrangler tail` line from 3.1
- The `deployments list` + `rollback` captures from 3.2 (or the documented-gap equivalent)
- The fully populated table from 3.3 with your own measured numbers
- The three-sentence reflection from 3.4

---

## Bonus Task — Custom Domain or D1/R2/Durable Objects (2 pts)

Pick **one**:

**Option A — Routing beyond `workers.dev`.** Attach your Worker to a Custom Domain you control (a zone on Cloudflare). If you have no domain, write the full procedure — what `wrangler.toml` looks like, what DNS records Cloudflare creates, what cert is provisioned — and show the `routes` block:

```toml
# YOUR TASK: routes block for a custom domain you control (or document precisely)
[[routes]]
pattern        = "___"            # YOUR TASK: e.g. api.example.com
custom_domain  = true
```

**Option B — A second state primitive.** Add **D1**, **R2**, or a **Durable Object**, bind it, and use it from one route.

```bash
# YOUR TASK: pick ONE
npx wrangler d1 create ___        # SQLite per region
npx wrangler r2 bucket create ___ # blob storage, no egress fees
# Durable Objects need a class export — see the docs
```

Then bind in `wrangler.toml` and call the binding from a new route. In `docs/LAB17.md`, write **one paragraph** justifying why you'd pick it over KV for the use case you implemented (consistency? joins? blobs? coordination?).

---

## How to Submit

```bash
git switch -c lab17
git add edge-api/ docs/LAB17.md
git commit -m "feat(lab17): cloudflare worker edge API + K8s comparison"
git push -u origin lab17
```

Open **two** PRs:

- `your-fork:lab17` → `course-repo:master` *(reviewed)*
- `your-fork:lab17` → `your-fork:master` *(merges into your own main when done)*

Include the live `workers.dev` URL in the PR description if you deployed; otherwise reference the documented-gap section in `docs/LAB17.md`. **Never commit secret values.**

PR checklist:

```text
- [ ] Task 1 done — scaffold, fetch handler, 3 routes + 404 + 405, local run, (deploy or documented gap)
- [ ] Task 2 done — var, ≥2 secrets, KV namespace + counter route, round-trip CLI
- [ ] Task 3 done — wrangler tail capture, deployments list + rollback, K8s-vs-Workers table filled, reflection
- [ ] Bonus done — Custom Domain config OR D1/R2/Durable Object wired (with justification)
```

---

## Acceptance Criteria

### Task 1 (4 pts)
- ✅ Wrangler 4.95+ installed; `whoami` works (if account) or gap documented
- ✅ `wrangler.toml` has `name`, `main`, `compatibility_date` filled with student-picked values
- ✅ `fetch` handler implements `/`, `/health`, `/echo` (GET 405, POST echo), and JSON 404
- ✅ All five local `curl` captures present in `docs/LAB17.md`
- ✅ Deploy capture against `workers.dev` (with real `edge.colo`) OR a documented-gap section

### Task 2 (3 pts)
- ✅ `wrangler.toml` has `[vars]` plus a `[[kv_namespaces]]` block with student-filled `binding` + real `id`
- ✅ `wrangler secret list` capture shows two named secrets (values not committed)
- ✅ Gated route returns 401 without auth and 200 with the right header
- ✅ `/counter` increments across three calls; KV CLI round-trip captured

### Task 3 (3 pts)
- ✅ `console.log()` present in the handler; one literal `wrangler tail` line in `docs/LAB17.md`
- ✅ `deployments list` + `rollback` capture (or gap documented)
- ✅ K8s-vs-Workers table fully populated with **the student's own Lab 9 measurements** + the student's Worker numbers
- ✅ Three-sentence reflection answering all three prompts

### Bonus Task (2 pts)
- ✅ Custom Domain config working or precisely documented, OR
- ✅ D1 / R2 / Durable Object created, bound, and used from a route — with a one-paragraph justification

---

## Rubric

| Task | Points | Criteria |
|---|---:|---|
| **Task 1** — Scaffold, build, deploy | **4** | Handler + routes correct, local run captured, deploy or documented gap |
| **Task 2** — Config, secrets, KV | **3** | Var + 2 secrets + KV counter all working, no values leaked |
| **Task 3** — Observability + comparison | **3** | Tail capture, deployments/rollback, **student-measured** comparison table, reflection |
| **Bonus** — Custom Domain / second state primitive | **2** | One option implemented or precisely documented |
| **Total** | **12** | 10 main + 2 bonus |

**Grading:**
- **10/10 main:** Worker deployed (or gap clearly justified), KV persistence shown, comparison table backed by real numbers, reflection is concrete
- **8–9/10:** Working Worker, minor gaps in evidence or analysis
- **6–7/10:** Basic deploy works but missing KV, observability, or comparison depth
- **<6/10:** Incomplete implementation

---

## Resources

<details>
<summary>📚 Core Cloudflare Workers Docs</summary>

- [Cloudflare Workers overview](https://developers.cloudflare.com/workers/)
- [Get started with Wrangler](https://developers.cloudflare.com/workers/get-started/guide/)
- [Wrangler v3 → v4 migration (local-by-default)](https://developers.cloudflare.com/workers/wrangler/migration/update-v3-to-v4/)
- [Wrangler commands](https://developers.cloudflare.com/workers/wrangler/commands/)
- [Workers pricing (free tier: 100k req/day)](https://developers.cloudflare.com/workers/platform/pricing/)
- [How Workers works (V8 isolates)](https://developers.cloudflare.com/workers/reference/how-workers-works/)

</details>

<details>
<summary>🔐 Config, Secrets & State</summary>

- [Environment variables](https://developers.cloudflare.com/workers/configuration/environment-variables/)
- [Secrets](https://developers.cloudflare.com/workers/configuration/secrets/)
- [Workers KV](https://developers.cloudflare.com/kv/) · [D1](https://developers.cloudflare.com/d1/) · [R2](https://developers.cloudflare.com/r2/) · [Durable Objects](https://developers.cloudflare.com/durable-objects/)
- [Choosing a storage product](https://developers.cloudflare.com/workers/platform/storage-options/)
- [Request API and `request.cf`](https://developers.cloudflare.com/workers/runtime-apis/request/)

</details>

<details>
<summary>📊 Observability & Deployments</summary>

- [Observability overview](https://developers.cloudflare.com/workers/observability/)
- [`wrangler tail`](https://developers.cloudflare.com/workers/observability/logs/real-time-logs/)
- [Versions & Deployments](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/)
- [Rollbacks](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/)

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs)</summary>

- **No filesystem in a V8 isolate.** `import fs from "node:fs"` throws at deploy. There is no `/tmp`. If you need to persist anything, it's KV/D1/R2/DO or nothing.
- **No Node APIs by default.** `Buffer`, `process`, `crypto` (Node flavor) are not present. To use a subset, add `compatibility_flags = ["nodejs_compat"]` to `wrangler.toml` — this is opt-in for a reason; the V8 isolate is not Node.
- **KV is eventually consistent.** A `put` followed immediately by a `get` from a different PoP can return the old value for **up to ~60 seconds**. Fine for counters and flags; wrong for "did the user click the buy button". Use Durable Objects when you need read-your-writes.
- **`Response.json()` Content-Type.** Auto-set since `compatibility_date: 2022-01-31`. If you pinned an older date (or copy-pasted ancient examples), you have to set `content-type: application/json` by hand. Pin a recent date in `wrangler.toml`.
- **`wrangler dev` is local by default in 4.x.** It runs `workerd` on your laptop — `request.cf` is a stub, KV is a SQLite-backed local emulator, secrets come from `.dev.vars`. Use `wrangler dev --remote` only if you need real edge metadata in dev (counts against quota).
- **`wrangler secret put` requires the Worker to exist on Cloudflare first.** If you haven't run `wrangler deploy` once, the secret command fails. Deploy a stub, then add secrets, then deploy the real version.
- **`workers.dev` subdomain is one-time-claim per account.** First deploy prompts you to pick `<you>.workers.dev`. You can't change it later without account-level support.
- **`request.cf?.colo` is `undefined` in local dev** (or a constant `"TBS"` stub). Always optional-chain.

</details>

<details>
<summary>🐍 Optional: Python Workers</summary>

- [Python Workers](https://developers.cloudflare.com/workers/languages/python/) — runs Pyodide; **no C extensions** (no NumPy, no Pillow). If you went Python in Lab 1 and want to keep that path, it's possible but constrained.
- [Python Worker packages](https://developers.cloudflare.com/workers/languages/python/packages/)

</details>

---

## Looking Ahead

| Lab | What it adds beyond Lab 17 |
|---:|---|
| 18 | Reproducible builds with Nix — the other bonus / exam-alternative lab. Together: 20% of the grade, full exam replacement |
| — | Workers AI, R2 + R2 Data Catalog, Hyperdrive, Pages Functions — the rest of the Cloudflare developer platform if you want to go deeper after the course |

**Good luck.** 🌍

> **Remember:** V8 isolates ≠ containers. Workers wins on cold start and price floor for globally distributed APIs; Kubernetes wins on long-running, stateful, native, multi-service workloads. Name the workload first, pick the runtime last.
