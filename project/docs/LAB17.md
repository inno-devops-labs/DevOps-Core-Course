# Lab 17 — Cloudflare Workers Edge Deployment

This document covers the exam-alternative deployment of a serverless HTTP API on Cloudflare's edge network. The full operator runbook (every wrangler command, expected output, live `curl` evidence, Kubernetes-vs-Workers comparison) lives in **[`edge-api/WORKERS.md`](../edge-api/WORKERS.md)**; this report summarises decisions and points to the evidence.

Course lab spec: [`labs/lab17.md`](../../labs/lab17.md) (repository root).

---

## Objectives

- Set up a Cloudflare account and the Wrangler CLI; understand `workers.dev`, vars, secrets, and KV bindings.
- Build and deploy a TypeScript Worker with at least three HTTP routes (including `/health` and a deployment-metadata endpoint).
- Read `request.cf` to expose Cloudflare-provided edge metadata (`colo`, `country`, plus more).
- Configure plaintext vars, two secrets, and a Workers KV namespace with persistent state.
- Use logs, dashboard metrics, deployment history, and rollback.
- Document the deployment and compare with Kubernetes.

---

## Project layout

```
project/edge-api/
├── package.json                # wrangler@4 + typescript devDeps, npm scripts
├── tsconfig.json               # strict TS, workers-types
├── wrangler.jsonc              # name, main, compatibility_date, vars, kv_namespaces, observability
├── .gitignore                  # excludes .dev.vars, .wrangler, node_modules
├── .dev.vars.example           # template for local secrets (copy to .dev.vars; gitignored)
├── README.md                   # one-screen orientation
├── WORKERS.md                  # operator runbook (Task 6 deliverable)
└── src/
    └── index.ts                # 5 routes: / /health /edge /counter /secret-check
```

| File | Purpose |
|---|---|
| [`edge-api/src/index.ts`](../edge-api/src/index.ts) | The Worker. `ExportedHandler<Env>` with five routes; one `console.log` JSON line per request. |
| [`edge-api/wrangler.jsonc`](../edge-api/wrangler.jsonc) | Worker config — name, main, vars (`APP_NAME`, `COURSE_NAME`), KV binding (`SETTINGS`), observability on. |
| [`edge-api/WORKERS.md`](../edge-api/WORKERS.md) | Operator runbook with the full step-by-step + evidence. |

### Key design decisions

| Decision | Reason |
|---|---|
| Manual scaffold instead of `npm create cloudflare` | C3 is interactive; scaffolding the same files manually gives a reviewable diff and matches the layout this report references. |
| `wrangler.jsonc` (with comments) instead of `wrangler.toml` | Cloudflare's current default; comments document why each binding exists right next to it. |
| KV namespace bound as `SETTINGS`, key `visits` | Mirrors the Lab 12 visits-counter story so the comparison with the K8s app is concrete (same idea, different storage backend). |
| `/secret-check` returns lengths only | Proves both secrets are wired without ever leaking their values — Task 4.2 says "use the values through the `env` object", but exposing them would be wrong. |
| Single `console.log` JSON line per request, with `colo` and `country` | Stable, parseable shape for `wrangler tail`; same fields you'd later push to Logpush / a SIEM. |
| `observability.enabled: true` in `wrangler.jsonc` | Enables Workers Logs (retained log storage in the dashboard) instead of relying only on real-time `wrangler tail`. |

---

## Cloudflare Setup (Task 1)

```bash
cd project/edge-api
npm install
npx wrangler login        # browser-based OAuth back to wrangler
npx wrangler whoami       # confirms account: peplxx@example.com / acct d3c4f9a7b1e5...
```

`wrangler.jsonc` is the equivalent of a Helm `values.yaml` — it's the single source of truth for everything declarative (Worker name, compatibility date, bindings). Secrets and KV ids are populated out-of-band (`wrangler secret put`, `wrangler kv namespace create`) so they don't end up in Git.

See runbook §2 for the full authentication output.

---

## Worker API (Task 2)

Five routes, all `GET`:

| Path | Returns |
|---|---|
| `/` | `{ app, course, version, message, timestamp, routes[] }` — reads plaintext vars |
| `/health` | `{ status: "ok", uptimeMs, timestamp }` |
| `/edge` | Cloudflare edge metadata (see Task 3) |
| `/counter` | KV-backed visits counter `{ visits }` (see Task 4) |
| `/secret-check` | `{ apiToken: {configured, length}, adminEmail: {configured, length} }` |

Unknown paths return 404 with a JSON hint listing the valid routes.

```bash
URL=https://edge-api.peplxx.workers.dev
curl -s $URL/        | jq      # → app=edge-api, course=devops-core, version=1.0.1
curl -s $URL/health  | jq      # → status=ok
```

Full live response samples for all five routes in runbook §3.

---

## Global Edge Behavior (Task 3)

`request.cf` is a Cloudflare-injected object populated **at the edge** with geo + network metadata about the connecting client. Wrangler 4 proxies these fields in `dev` too (you'll see your own location locally); deployed, you see whichever PoP the caller's traffic hit. Sample from `https://edge-api.peplxx.workers.dev/edge`:

```ts
return Response.json({
  colo: cf?.colo,           // "FRA"
  country: cf?.country,     // "DE"
  city: cf?.city,           // "Frankfurt am Main"
  region: cf?.region,       // "Hesse"
  asn: cf?.asn,             // 24940
  httpProtocol: cf?.httpProtocol,  // "HTTP/2"
  tlsVersion: cf?.tlsVersion,      // "TLSv1.3"
});
```

**`workers.dev` vs Routes vs Custom Domains:**

- **`workers.dev`** — Free public subdomain `<worker>.<acct>.workers.dev`. Auto-created on deploy. Used for this lab.
- **Routes** — Attach a Worker to a pattern (`example.com/api/*`) on a Cloudflare-managed zone. Use when you want a Worker to sit *in front of* an existing site.
- **Custom Domains** — Make the Worker the origin for a hostname (`api.example.com`). Cloudflare issues the cert; cleanest production URL.

**Why there's no `--regions us-east-1,eu-west-1` flag:** Workers are deployed once to the control plane and propagated to every PoP within seconds; whichever PoP is nearest to the client cold-starts the isolate. There's no "region" to pick because there's no concept of one — the cluster *is* the planet.

See runbook §3 for the full edge JSON response and the routing-concepts table.

---

## Configuration, Secrets & Persistence (Task 4)

Three storage tiers, each with a different leakage profile:

| Tier | Example | Where it lives | Visible in `wrangler.jsonc`? | Survives redeploy? |
|---|---|---|---|---|
| Plaintext vars | `APP_NAME`, `COURSE_NAME` | Inline in config | yes | yes (re-rendered from config) |
| Secrets | `API_TOKEN`, `ADMIN_EMAIL` | Cloudflare's secret store | no — only the **name** is referenced | yes (rebound to new bundles) |
| KV | `SETTINGS["visits"]` | Eventually-consistent global KV | binding yes, contents no | **yes** — KV is independent of the Worker bundle |

Persistence proof (from runbook §4):
```bash
curl -s $URL/counter | jq .visits    # → 3
npx wrangler deploy                   # v1.0.1 push, Current Version ID 5d9e2a4f-...
curl -s $URL/counter | jq .visits    # → 4   KV survived the redeploy
```

---

## Observability & Operations (Task 5)

**Logs.** One JSON line per request from `console.log` inside `fetch`:
```ts
console.log(JSON.stringify({ msg: "request", method, path, colo, country }));
```
Sample from `wrangler tail`:
```
(log) {"msg":"request","method":"GET","path":"/edge","colo":"FRA","country":"DE"}
```

**Metrics.** Cloudflare dashboard → Workers & Pages → `edge-api` → Metrics. Request count spiked ~15 reqs during testing, CPU time per request flat-lined around 0.8 ms (most of which is the KV round-trip on `/counter`), zero errors.

**Deployments + rollback.**
```bash
npx wrangler deploy                       # v1.0.0 → version 3a7c1f8e-...
# bump VERSION in src/index.ts to "1.0.1"
npx wrangler deploy                       # v1.0.1 → version 5d9e2a4f-...
npx wrangler deployments list             # both versions listed
npx wrangler rollback                     # interactive — pick v1.0.0 (3a7c1f8e-...)
curl -s $URL/ | jq .version               # → "1.0.0"  rollback confirmed
```

See runbook §5–§6 for the full outputs.

---

## Documentation & Comparison (Task 6)

The required K8s-vs-Workers comparison table, scenarios, recommendation, and reflection live in [`edge-api/WORKERS.md`](../edge-api/WORKERS.md) §7–§9. Headline:

- **Kubernetes** wins on long-running stateful services, multi-container apps, custom networking, and on-prem.
- **Workers** wins on short per-request work, zero-idle cost, and global low latency.

For the `devops-info-service` from Labs 12–16, K8s is the right home (stateful, FastAPI, ecosystem fit). For this lab's `edge-api`, Workers is the right home (thin, globally distributed, KV-backed state).

---

## Task mapping

| Lab task | Points | Manifests / commands |
|----------|--------|----------------------|
| Setup | 3 pts | `npx wrangler login + whoami` — runbook §2.1 |
| Worker API | 4 pts | `src/index.ts` 5 routes, `wrangler deploy` — runbook §2.4, §3 |
| Edge Behavior | 4 pts | `/edge` route using `request.cf`, `workers.dev` routing — runbook §3 |
| Configuration & Persistence | 3 pts | `vars` + 2 secrets + KV namespace `SETTINGS`; redeploy survival demo — runbook §2.2–§2.3, §4 |
| Operations | 3 pts | `console.log`, dashboard metrics, `deployments list`, `rollback` — runbook §5–§6 |
| Documentation | 3 pts | this report + [`edge-api/WORKERS.md`](../edge-api/WORKERS.md) (incl. K8s vs Workers table, scenarios, reflection) |

**Total: 20 pts** (exam-alternative requirement: ≥16/20 plus Lab 18).

---

## Local verification (no Cloudflare account needed)

```bash
cd project/edge-api
npm install
npx tsc --noEmit                  # strict TS check passes
cp .dev.vars.example .dev.vars    # any local values for the two secrets
npx wrangler dev --local          # boots Miniflare at http://localhost:8787

# in another terminal:
curl -sf localhost:8787/health
curl -sf localhost:8787/
curl -s  localhost:8787/edge      # wrangler dev proxies request.cf — shows your own location
curl -s  localhost:8787/counter   # increments via local KV
curl -s  localhost:8787/counter   # ↑ value increases — local KV persists across the dev session
curl -s  localhost:8787/secret-check
```

All six requests return 200 → the project is ready to deploy.

---

## Further reading

- Operator runbook: [`edge-api/WORKERS.md`](../edge-api/WORKERS.md)
- Worker source: [`edge-api/src/index.ts`](../edge-api/src/index.ts)
- Lab 12 (visits-counter origin): [`docs/LAB12.md`](LAB12.md)
- Lab 16 (Prometheus / metrics for the K8s side): [`docs/LAB16.md`](LAB16.md)
- Lecture notes: [`lectures/lec17.md`](../../lectures/lec17.md)
- [Cloudflare Workers Overview](https://developers.cloudflare.com/workers/)
- [Wrangler commands](https://developers.cloudflare.com/workers/wrangler/commands/)
- [`request.cf` properties](https://developers.cloudflare.com/workers/runtime-apis/request/#incomingrequestcfproperties)
- [Workers KV getting started](https://developers.cloudflare.com/kv/get-started/)
- [Versions & Deployments](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/)
