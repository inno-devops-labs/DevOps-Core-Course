# Lab 17 — Cloudflare Workers Edge Deployment

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Edge%20Computing-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![type](https://img.shields.io/badge/type-Exam%20Alternative-purple)

> Build and deploy a serverless HTTP API on Cloudflare's global edge network using Cloudflare Workers, then compare the model against the Kubernetes stack you built across Labs 8-16.

## Overview

Cloudflare Workers is a serverless **edge** platform: your code runs in a lightweight **V8 isolate** (not a container, not a VM) inside an already-running process at 330+ points of presence worldwide. Cold start is **<5 ms**, the memory floor is ~3 MB, and there is no region to pick — every deploy is global by default. This is the opposite end of the abstraction spectrum from the Kubernetes you've spent the course mastering.

In this lab you'll scaffold a Worker with **Wrangler 4.x**, build a small HTTP API, deploy it to a public `workers.dev` URL, wire in config/secrets/state via platform **bindings**, observe it in production, and write up an honest Kubernetes-vs-Workers comparison.

**This is a bonus / Exam Alternative lab.** Complete both Lab 17 (12 pts) and Lab 18 (12 pts) to the required bar to replace the final exam. See the lecture 16 finale for where edge isolates sit on the deployment spectrum.

**What You'll Learn:**
- Edge computing and the V8-isolate execution model (vs containers)
- Serverless deployment workflow with Wrangler 4.x (local-first by default)
- Global request metadata via `request.cf`
- Configuration, secrets, and edge-attached state (Workers KV)
- Observability (logs, metrics) and version/rollback management
- Kubernetes vs Workers trade-offs — when each is the right tool

**Prerequisites:**
- Git
- Node.js 18+ and npm
- A free Cloudflare account
- Basic HTTP/JSON familiarity

**Important:** This lab does **not** deploy your Docker image from Lab 2. Cloudflare Workers is a serverless runtime, not a Docker host — there is no `Dockerfile`, no ingress, no HPA. You will build a Workers-native API that preserves the same operational concerns (routes, health checks, config, state, logs, deploys, public access) in the edge model.

> **Regional connectivity note:** In some countries and networks, including Russia, Cloudflare services may be partially restricted. If commands such as `npx wrangler whoami` or `npx wrangler deploy` fail with vague network errors, the problem may be your network path rather than your code. If you use a VPN, prefer full-tunnel / global-routing mode — proxy or split-tunnel setups can let Node.js and Wrangler traffic bypass the VPN and hit the restricted network.

**Tech Stack:** Cloudflare Workers (V8 isolates / workerd) | Wrangler **4.x** | TypeScript | Workers KV | `workers.dev`

> All terminal output in this lab is **illustrative** — your account names, namespace IDs, colos, and version IDs will differ. Do not copy IDs from the examples.

---

## Exam Alternative Requirements

| Requirement | Details |
|-------------|---------|
| **Deadline** | 1 week before the exam date |
| **Minimum Score** | 10/12 on **each** of Lab 17 and Lab 18 |
| **Must Complete** | Both Lab 17 **and** Lab 18 |
| **Total Points** | Together they form the **exam replacement** option |

> Taken on its own, Lab 17 is a **bonus** lab: **10 pts** of main tasks + a **2 pt** bonus task = **12 pts max**.

---

## Tasks

> **How this lab is structured:** 3 main tasks (4 + 3 + 3 = **10 pts**) plus one **2 pt** bonus task. Skeletons below use `// YOUR-TASK:` markers — fill them in. Do not just paste the hints verbatim; they are minimal scaffolds.

### Task 1 — Scaffold, Build & Deploy a Worker API (4 pts)

**Objective:** Set up Cloudflare + Wrangler 4.x, build a small HTTP API, run it locally, and deploy it globally.

**Requirements:**

1. **Account & project**
   - Create a free Cloudflare account and confirm you can reach **Workers** in the dashboard.
   - Scaffold a project with C3 (`create-cloudflare`), the **"Hello World" / Worker only** template, **TypeScript**.
   - Authenticate Wrangler and verify with `npx wrangler whoami`.
   - Be able to explain what `wrangler.jsonc` and a `workers.dev` subdomain are.

2. **Implement at least 3 routes**
   - `GET /health` → `{ "status": "ok" }` with HTTP 200.
   - `GET /` → JSON metadata about the deployment (app name, message, timestamp).
   - One more route of your choosing (you'll extend this in later tasks).
   - Return correct status codes and a `404` JSON for unknown paths.

3. **Run locally, then deploy**
   - Start local dev with `npx wrangler dev` (Wrangler 4.x runs **locally by default** — it executes your Worker in `workerd` on your machine; `--remote` is now opt-in).
   - Test routes with `curl`, confirm status codes and JSON.
   - Deploy with `npx wrangler deploy` and confirm the public `workers.dev` URL responds.

4. **Version control**
   - Commit the Worker project to Git with a clean history you can refer to later.

<details>
<summary>💡 Hints & skeleton</summary>

**Scaffold (Wrangler 4.x via C3):**
```bash
npm create cloudflare@latest -- edge-api
cd edge-api
```
Recommended choices: *Hello World* example → *Worker only* → *TypeScript* → Git: **Yes** → Deploy now: **No**.

**Authenticate:**
```bash
npx wrangler login      # OAuth in the browser
npx wrangler whoami     # verifies account + lists your workers.dev subdomain
npx wrangler --version  # confirm 4.x
```

**Generated layout to know:**
- `src/index.ts` — Worker source (the default `fetch` export)
- `wrangler.jsonc` — Worker configuration (name, main, compatibility_date, bindings)
- `package.json` — local scripts and dependencies

**`src/index.ts` skeleton:**
```ts
export interface Env {
  APP_NAME: string;          // plaintext var (Task 2)
  // YOUR-TASK: add secret + KV binding types in Task 2
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return Response.json({ status: "ok" });
    }

    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME ?? "edge-api",
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
      });
    }

    // YOUR-TASK: add your third route here

    return Response.json({ error: "Not Found" }, { status: 404 });
  },
};
```

**Local dev + deploy (illustrative output):**
```bash
npx wrangler dev          # local workerd; open http://localhost:8787
curl http://localhost:8787/health        # -> {"status":"ok"}
npx wrangler deploy
# Deployed edge-api triggers (illustrative)
#   https://edge-api.<your-subdomain>.workers.dev
curl https://edge-api.<your-subdomain>.workers.dev/health
```

Public URL format:
```text
https://<worker-name>.<your-subdomain>.workers.dev
```

**Resources:**
- [Workers overview](https://developers.cloudflare.com/workers/)
- [Get started with Wrangler](https://developers.cloudflare.com/workers/get-started/guide/)
- [Wrangler v3 → v4 migration (local-by-default)](https://developers.cloudflare.com/workers/wrangler/migration/update-v3-to-v4/)
- [Wrangler commands](https://developers.cloudflare.com/workers/wrangler/commands/)

</details>

---

### Task 2 — Edge Behavior, Config, Secrets & State (3 pts)

**Objective:** Show your Worker running on the global network, then configure it with a variable, secrets, and persistent KV state.

**Requirements:**

1. **Edge metadata endpoint**
   - Add `GET /edge` returning fields from `request.cf`: at minimum **`colo`** and **`country`**, plus one more (`asn`, `city`, `httpProtocol`, or `tlsVersion`).
   - Call your **deployed** URL and capture the JSON — this is your evidence that Cloudflare supplies request metadata at the edge.
   - Note: `request.cf` is populated on the real edge, **not** in `wrangler dev` by default.

2. **Plaintext variable**
   - Define at least 1 `var` in `wrangler.jsonc` and use it in a response.
   - Explain why plaintext vars are unsuitable for secrets.

3. **Secrets**
   - Create at least 2 secrets with `npx wrangler secret put`, read them via `env`, and never commit the values.

4. **Persistence with Workers KV**
   - Create a KV namespace, bind it in `wrangler.jsonc`, and store + retrieve at least one value (e.g. a `/counter` route).
   - Verify the value survives a **redeploy** and document how you checked.

<details>
<summary>💡 Hints & skeleton</summary>

**`/edge` route:**
```ts
if (url.pathname === "/edge") {
  return Response.json({
    colo: request.cf?.colo,            // e.g. "FRA"
    country: request.cf?.country,      // e.g. "DE"
    city: request.cf?.city,
    asn: request.cf?.asn,
    httpProtocol: request.cf?.httpProtocol,
    tlsVersion: request.cf?.tlsVersion,
  });
}
```
```bash
curl https://edge-api.<your-subdomain>.workers.dev/edge
# illustrative: {"colo":"FRA","country":"DE","httpProtocol":"HTTP/2", ...}
```

**Plaintext vars in `wrangler.jsonc`:**
```jsonc
{
  "vars": {
    "APP_NAME": "edge-api",
    "COURSE_NAME": "devops-core"
  }
}
```
Vars are stored in plaintext in config and the dashboard — anyone with read access sees them. Use **secrets** for tokens/credentials.

**Secrets (values are prompted, never written to Git):**
```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
npx wrangler secret list      # names only, not values
```

**Create + bind a KV namespace (Wrangler 4.x syntax):**
```bash
npx wrangler kv namespace create SETTINGS
# illustrative output -> add this to wrangler.jsonc:
```
```jsonc
{
  "kv_namespaces": [
    { "binding": "SETTINGS", "id": "<your-namespace-id>" }
  ]
}
```

**KV-backed counter + typed Env:**
```ts
export interface Env {
  APP_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

if (url.pathname === "/counter") {
  const visits = Number((await env.SETTINGS.get("visits")) ?? "0") + 1;
  await env.SETTINGS.put("visits", String(visits));
  return Response.json({ visits });
}
```

Verify persistence: hit `/counter` a few times, `npx wrangler deploy` again, hit it once more — the count should continue, not reset.

> KV is **eventually consistent**. For strongly-consistent or richer state, Workers also offers **D1** (SQLite), **R2** (S3-compatible blobs, no egress fees), and **Durable Objects** (strongly-consistent stateful actors). KV is the right primitive for flags/config/counters.

**Resources:**
- [Request API and `request.cf`](https://developers.cloudflare.com/workers/runtime-apis/request/)
- [Environment variables](https://developers.cloudflare.com/workers/configuration/environment-variables/)
- [Secrets](https://developers.cloudflare.com/workers/configuration/secrets/)
- [Workers KV getting started](https://developers.cloudflare.com/kv/get-started/)
- [Choosing a storage product (KV / D1 / R2 / DO)](https://developers.cloudflare.com/workers/platform/storage-options/)

</details>

---

### Task 3 — Observability, Operations & Comparison (3 pts)

**Objective:** Observe your Worker in production, manage versions/rollbacks, and document the model against Kubernetes.

**Requirements:**

1. **Logs**
   - Add at least 1 `console.log()` and view live output with `npx wrangler tail` (or in the dashboard). Capture an example entry.

2. **Metrics**
   - Open the Worker in the Cloudflare dashboard and review request counts / errors / CPU time. Briefly say what you looked at.

3. **Versions & rollback**
   - Deploy at least **2 versions**, view deployment history, and perform (or describe) a rollback.

4. **`WORKERS.md` write-up** containing:
   - **Deployment summary:** Worker URL, routes, config/bindings used.
   - **Evidence:** dashboard screenshot, an example `/edge` JSON response, a log or metrics screenshot.
   - **Kubernetes vs Workers comparison table** (fill every cell):

     | Aspect | Kubernetes | Cloudflare Workers |
     |--------|------------|--------------------|
     | Cold start | | |
     | Setup complexity | | |
     | Global distribution | | |
     | Cost at zero/low traffic | | |
     | State/persistence model | | |
     | Long-running / native binaries | | |
     | Best use case | | |

   - **When to use each** + your recommendation.
   - **Reflection:** what was easier than K8s, what felt more constrained, what changed because Workers is not a Docker host.

<details>
<summary>💡 Hints & skeleton</summary>

**Logging:**
```ts
console.log("path", url.pathname, "colo", request.cf?.colo);
```
```bash
npx wrangler tail        # streams live logs from the edge (illustrative)
```

**Versions & deployments (Wrangler 4.x):**
```bash
npx wrangler deploy                 # deploy v1, then change code and deploy v2
npx wrangler deployments list       # shows version IDs + timestamps (illustrative)
npx wrangler rollback               # roll back to the previous version
# or target one explicitly:
npx wrangler rollback <version-id>
```

**Facts to anchor your comparison (from the lecture):**
- Cold start: K8s pod = seconds (scheduling + image pull); Workers = **<5 ms** (V8 isolate).
- Memory floor: K8s = container request (e.g. 128 Mi); Workers ≈ 3 MB/isolate.
- Global: K8s = pick region(s); Workers = **all 330+ POPs by default**.
- Free tier: K8s = minikube only; Workers = **100k requests/day**, 10 ms CPU (Paid $5/mo = 10M req + 50 ms CPU, burstable).
- Long-running/native: K8s = anything; Workers = short CPU budget, no native binaries, no filesystem.

**Resources:**
- [Observability overview](https://developers.cloudflare.com/workers/observability/)
- [Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/)
- [Versions & deployments](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/)
- [Rollbacks](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/)
- [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/)

</details>

---

### Bonus Task — Custom Domain or D1/R2/Durable Objects (2 pts)

**Objective:** Go one step past `workers.dev` — either expose your Worker on a real domain *or* add a richer state primitive.

**Pick ONE:**

**Option A — Routing beyond `workers.dev`**
- Explain the difference between `workers.dev`, **Routes**, and **Custom Domains**.
- Attach your Worker to a Custom Domain (a domain on Cloudflare you control) **or**, if you have no domain, write a precise description of the steps and config and show the relevant `wrangler.jsonc`/dashboard config.

**Option B — A second state primitive**
- Add **D1** (`npx wrangler d1 create ...`), **R2** (`npx wrangler r2 bucket create ...`), or a **Durable Object**, bind it, and use it from one route.
- Explain why you'd pick it over KV for that use case (consistency, relational queries, blobs, or stateful coordination).

Document your choice in `WORKERS.md` with config + an illustrative request/response.

<details>
<summary>💡 Hints</summary>

**Routing concepts:**
- `workers.dev` — instant public URL, no domain needed.
- **Routes** — attach a Worker to traffic patterns on an existing Cloudflare **zone**.
- **Custom Domains** — make the Worker the origin for a domain/subdomain (Cloudflare manages the DNS + cert).

```jsonc
// Custom Domain example in wrangler.jsonc
{ "routes": [ { "pattern": "api.example.com", "custom_domain": true } ] }
```

**D1 (SQLite at the edge):**
```bash
npx wrangler d1 create edge-db
# add the binding it prints to wrangler.jsonc, then:
npx wrangler d1 execute edge-db --command "CREATE TABLE notes(id INTEGER PRIMARY KEY, body TEXT);"
```

**R2 (S3-compatible, no egress fees):**
```bash
npx wrangler r2 bucket create edge-assets
```

**Resources:**
- [`workers.dev` routing](https://developers.cloudflare.com/workers/configuration/routing/workers-dev/)
- [Routes and Custom Domains](https://developers.cloudflare.com/workers/configuration/routing/)
- [D1](https://developers.cloudflare.com/d1/) · [R2](https://developers.cloudflare.com/r2/) · [Durable Objects](https://developers.cloudflare.com/durable-objects/)

</details>

---

## How to Submit

1. **Create a branch** (e.g. `lab17`) inside your course repo/fork.
2. **Commit** your Worker project (`edge-api/` or similar) and `WORKERS.md` — secrets values must **not** be committed.
3. **Push** and open a PR/MR from `feature/lab17` → the course repo. Include the live `workers.dev` URL in the PR description and submit the link via Moodle.
4. **Verify** all files, screenshots, and the comparison table are present.

---

## Acceptance Criteria

### Main Tasks (10 points)

**Task 1 — Scaffold, Build & Deploy (4 pts):**
- [ ] Cloudflare account created; Wrangler 4.x authenticated (`whoami` works)
- [ ] Project scaffolded with C3 (Worker only, TypeScript)
- [ ] At least 3 routes including `GET /health` (200) and a JSON metadata route, with a `404` fallback
- [ ] Runs locally via `wrangler dev` and deploys to a public `workers.dev` URL
- [ ] Project committed to Git

**Task 2 — Edge, Config, Secrets & State (3 pts):**
- [ ] `/edge` endpoint returns `colo` + `country` + ≥1 more `request.cf` field, captured from the deployed URL
- [ ] ≥1 plaintext `var` used; explanation of why vars ≠ secrets
- [ ] ≥2 secrets created with Wrangler and read via `env` (values not committed)
- [ ] KV namespace created, bound, used, and persistence verified across a redeploy

**Task 3 — Observability, Ops & Comparison (3 pts):**
- [ ] Log entry captured via `wrangler tail` or dashboard
- [ ] A dashboard metric reviewed and described
- [ ] ≥2 versions deployed; deployment history viewed; rollback performed or described
- [ ] `WORKERS.md` complete: deployment summary, evidence, **filled** K8s-vs-Workers table, when-to-use + reflection

### Bonus Task (2 points)
- [ ] One of: Custom Domain/Routes configured (or precisely documented), **or** D1/R2/Durable Object added, bound, and used from a route
- [ ] Justification for the choice documented in `WORKERS.md`

---

## Rubric (12 pts max)

| Criteria | Points |
|----------|--------|
| Task 1 — Scaffold, Build & Deploy | 4 |
| Task 2 — Edge, Config, Secrets & State | 3 |
| Task 3 — Observability, Ops & Comparison | 3 |
| **Main total** | **10** |
| Bonus — Custom Domain or D1/R2/Durable Objects | 2 |
| **Total** | **12** |

**Grading:**
- **10/10 main:** Worker deployed globally, KV persistence proven, strong edge evidence, thorough and honest comparison
- **8-9/10:** Working Worker with good docs; minor gaps in evidence or analysis
- **6-7/10:** Basic deployment works but missing KV, observability, or comparison depth
- **<6/10:** Incomplete implementation
- **+2 bonus:** a working/clearly-documented Custom Domain or second state primitive

---

## Resources

<details>
<summary>📚 Core Cloudflare Workers Docs</summary>

- [Cloudflare Workers Overview](https://developers.cloudflare.com/workers/)
- [Get started with Wrangler](https://developers.cloudflare.com/workers/get-started/guide/)
- [Wrangler v3 → v4 migration guide](https://developers.cloudflare.com/workers/wrangler/migration/update-v3-to-v4/)
- [Wrangler commands](https://developers.cloudflare.com/workers/wrangler/commands/)
- [Workers pricing (free tier: 100k req/day)](https://developers.cloudflare.com/workers/platform/pricing/)

</details>

<details>
<summary>🌍 Edge Runtime & Routing</summary>

- [How Workers works (V8 isolates)](https://developers.cloudflare.com/workers/reference/how-workers-works/)
- [Request API and `request.cf`](https://developers.cloudflare.com/workers/runtime-apis/request/)
- [`workers.dev`](https://developers.cloudflare.com/workers/configuration/routing/workers-dev/)
- [Routes and Custom Domains](https://developers.cloudflare.com/workers/configuration/routing/)

</details>

<details>
<summary>🔐 Config, Secrets & State</summary>

- [Environment variables](https://developers.cloudflare.com/workers/configuration/environment-variables/)
- [Secrets](https://developers.cloudflare.com/workers/configuration/secrets/)
- [Workers KV](https://developers.cloudflare.com/kv/) · [D1](https://developers.cloudflare.com/d1/) · [R2](https://developers.cloudflare.com/r2/) · [Durable Objects](https://developers.cloudflare.com/durable-objects/)
- [Choosing a storage product](https://developers.cloudflare.com/workers/platform/storage-options/)

</details>

<details>
<summary>📊 Observability & Deployments</summary>

- [Observability overview](https://developers.cloudflare.com/workers/observability/)
- [Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/)
- [Versions & Deployments](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/)
- [Rollbacks](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/)

</details>

<details>
<summary>🐍 Optional Python Track</summary>

- [Python Workers](https://developers.cloudflare.com/workers/languages/python/) (Pyodide; no C extensions)
- [Python Worker packages](https://developers.cloudflare.com/workers/languages/python/packages/)

</details>

---

**Good luck!** 🌍

> **Remember:** V8 isolates ≠ containers — a language-layer sandbox with a <5 ms cold start and a ~3 MB memory floor. Workers win on latency and price floor for globally distributed APIs and lightweight edge logic; Kubernetes wins on long-running, stateful, native, multi-service workloads. Name the workload first, pick the runtime last.
