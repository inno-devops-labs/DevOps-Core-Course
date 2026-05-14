# LAB17 — Cloudflare Workers Edge Deployment

## 1. Task 1 — Cloudflare Setup

### Account and project creation

Created a Cloudflare account at cloudflare.com and accessed the Workers section from the dashboard. Initialized the project with:

```bash
npm create cloudflare@latest -- edge-api
cd edge-api
```

Choices during setup: Hello World example, Worker only, TypeScript, Git: Yes, Deploy now: No.

### Wrangler authentication

```bash
npx wrangler login
npx wrangler whoami
```

**Evidence**

![whoami](../screenshots/whoami.png)

### Key files in the generated project

- `src/index.ts` — Worker source code
- `wrangler.jsonc` — Worker configuration (name, vars, KV bindings)
- `package.json` — scripts and devDependencies

### Platform concepts

`workers.dev` is a shared subdomain Cloudflare assigns to every account. Each deployed Worker gets a URL of the form `https://<worker-name>.<account>.workers.dev`. Bindings are the mechanism for attaching platform resources (vars, secrets, KV namespaces, R2 buckets) to a Worker at runtime through the `env` parameter.

---

## 2. Task 2 — Worker API

### Routes implemented

| Path | Method | Description |
|------|--------|-------------|
| `/` | GET | App name, course, timestamp |
| `/health` | GET | Health status |
| `/edge` | GET | Edge metadata from `request.cf` |
| `/counter` | GET | KV-backed visit counter |

See `src/index.ts` for the full implementation.

### Local development

```bash
npx wrangler dev
curl http://localhost:8787/health
curl http://localhost:8787/
```

**Evidence**

![local-dev](../screenshots/local-dev.png)

### Deployment

```bash
npx wrangler deploy
```

**Evidence**

![deploy](../screenshots/deploy.png)

### Version control

The project is committed under `edge-api/` in the main course repository. Each deploy creates a versioned entry in Cloudflare's deployment history.

---

## 3. Task 3 — Global Edge Behavior

### Edge metadata endpoint

`GET /edge` returns data from `request.cf`:

```json
{
  "colo": "WAW",
  "country": "PL",
  "city": "Warsaw",
  "asn": 12345,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3"
}
```

**Evidence**

![edge-response](../screenshots/edge-response.png)

### How Workers distributes execution globally

Cloudflare operates 300+ points of presence worldwide. When a request hits any Cloudflare data center, the Worker is instantiated in that same location using a V8 isolate. There is no concept of "deploy to region X" — the code is available everywhere simultaneously the moment `wrangler deploy` completes. In contrast, VM or PaaS platforms require the operator to choose specific regions and manage cross-region failover manually.

### Routing concepts

- `workers.dev` — a free subdomain Cloudflare provides per account; sufficient for development and testing.
- Routes — pattern-based rules that attach a Worker to traffic destined for a zone already on Cloudflare (e.g., `example.com/api/*`).
- Custom Domains — make the Worker the origin for an entire domain or subdomain; requests to that host are served by the Worker without a route pattern.

This lab uses `workers.dev`.

---

## 4. Task 4 — Configuration, Secrets, and Persistence

### Plaintext environment variables

Defined in `wrangler.jsonc`:

```json
"vars": {
  "APP_NAME": "edge-api",
  "COURSE_NAME": "devops-core"
}
```

Used in the `GET /` response. Plaintext vars are visible in `wrangler.jsonc` and in the dashboard, so they are not suitable for secrets such as tokens or passwords.

### Secrets

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

Secret values are stored encrypted in Cloudflare and injected at runtime through `env.API_TOKEN` and `env.ADMIN_EMAIL`. They are never written to `wrangler.jsonc` or committed to Git.

**Evidence**

![secrets](../screenshots/secrets.png)

### Workers KV namespace

```bash
npx wrangler kv namespace create SETTINGS
```

The returned namespace ID was added to `wrangler.jsonc`:

```json
"kv_namespaces": [
  {
    "binding": "SETTINGS",
    "id": "<namespace-id>"
  }
]
```

`GET /counter` reads the current visit count from `env.SETTINGS`, increments it, writes it back, and returns the new value.

### Persistence verification

After redeploying, `GET /counter` continued returning incrementing values from the previous session, confirming the KV data persisted across deployments.

**Evidence**

![counter-persist](../screenshots/counter-persist.png)

---

## 5. Task 5 — Observability and Operations

### Console logs

`console.log("request", request.method, url.pathname, "colo", request.cf?.colo)` is called for every request.

Viewed with:

```bash
npx wrangler tail
```

**Evidence**

![tail-logs](../screenshots/tail-logs.png)

### Metrics

Opened the Worker in the Cloudflare dashboard under Workers & Pages → edge-api → Metrics. Reviewed the requests-per-minute graph and the CPU time histogram. The metrics show successful request counts and confirm no errors were recorded during testing.

**Evidence**

![metrics](../screenshots/metrics.png)

### Deployment history

```bash
npx wrangler deployments list
```

Deployed two versions: initial deployment (routes `/`, `/health`, `/edge`) and a second deployment adding `/counter` and secrets. Both versions are listed with timestamps and deployment IDs.

To roll back to the previous version:

```bash
npx wrangler rollback
```

Rollback reverts the active deployment to the previous version without rebuilding or redeploying code.

**Evidence**

![deployments](../screenshots/deployments.png)

---

## 6. Task 6 — Documentation and Comparison

See `WORKERS.md` in the `edge-api/` directory for the full deployment summary, Kubernetes vs Workers comparison table, and reflection.
