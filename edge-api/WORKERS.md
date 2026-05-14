# Lab 17 — Cloudflare Workers Edge Deployment

## Deployment Summary

**Worker URL:** [https://edge-api.maria-devops.workers.dev](https://edge-api.maria-devops.workers.dev)

**Main Routes:**

* `/` — basic app info
* `/health` — health check
* `/edge` — edge metadata
* `/counter` — KV-backed counter
* `/secrets-test` — secrets validation endpoint

**Tech Stack:** Cloudflare Workers, Wrangler CLI, TypeScript, Workers KV

---

## Task 1 — Setup

### Project Creation

```bash
npm create cloudflare@latest edge-api
cd edge-api
```

### Authentication

```bash
npx wrangler login
npx wrangler whoami
```

---

## Task 2 — Worker API

### Implementation

```ts
export interface Env {
  APP_NAME: string;
  SETTINGS: KVNamespace;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return Response.json({ status: "ok" });
    }

    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/edge") {
      return Response.json({
        colo: request.cf?.colo,
        country: request.cf?.country,
        city: request.cf?.city,
        asn: request.cf?.asn,
        httpProtocol: request.cf?.httpProtocol,
        tlsVersion: request.cf?.tlsVersion,
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return Response.json({ visits });
    }

    if (url.pathname === "/secrets-test") {
      return Response.json({
        hasToken: !!env.API_TOKEN,
        admin: env.ADMIN_EMAIL
      });
    }

    return new Response("Not Found", { status: 404 });
  },
};
```

### Local Run

```bash
npx wrangler dev
```

### Deploy

```bash
npx wrangler deploy
```

---

## Task 3 — Edge Behavior (REAL OUTPUT)

### Example Response (/edge)

```json
{
  "colo": "WAW",
  "country": "PL",
  "city": "Warsaw",
  "asn": 57043,
  "httpProtocol": "HTTP/1.1",
  "tlsVersion": "TLSv1.3"
}
```

### Explanation

Cloudflare Workers executes code on the nearest edge location automatically. Routing is handled by Cloudflare Anycast network, so there is no manual region selection like in Kubernetes or VM-based platforms.

---

## Task 4 — Config, Secrets & KV

### KV Namespace

* Created successfully via Wrangler
* ID: `892be24b779d4eb08e25e097cb1389cf`

### Secrets

* `API_TOKEN` stored in Cloudflare Secrets
* `ADMIN_EMAIL` stored in Cloudflare Secrets

### Secrets Test Output

```json
{
  "hasToken": true,
  "admin": "my-secret-123"
}
```

⚠️ Secrets are not stored in Git or codebase, only in Cloudflare environment.

### Persistence Verification

```json
{"visits": 1}
```

Counter persists via Workers KV and increments across requests.

---

## Task 5 — Observability

### Logging

* Supported via `wrangler tail`

### Deployments

* Version ID: `a274e4d1-5b93-4cdb-af2d-6b18e391b159`

---

## Kubernetes vs Cloudflare Workers

| Aspect              | Kubernetes      | Cloudflare Workers   |
| ------------------- | --------------- | -------------------- |
| Setup complexity    | High            | Very low             |
| Deployment speed    | Medium          | Instant              |
| Global distribution | Manual          | Automatic            |
| Cost (small apps)   | Higher          | Very low             |
| State model         | Volumes/DB      | KV / Durable Objects |
| Control             | Full            | Limited              |
| Best use case       | Complex systems | Edge APIs            |

---

## When to Use Each

### Kubernetes

* Microservices
* Stateful distributed systems
* Full infrastructure control

### Workers

* Edge APIs
* Lightweight serverless logic
* Low-latency global endpoints

---

## Reflection

**Easier than Kubernetes:**

* No infrastructure provisioning
* Instant global deployment
* Built-in routing

**Constraints:**

* No Docker support
* Limited runtime environment

---

## Evidence

* `/health` → OK
* `/edge` → WAW, PL
* `/counter` → KV working
* `/secrets-test` → secrets validated

---

## Checklist

* [x] Worker created
* [x] API implemented
* [x] Deployed to workers.dev
* [x] Edge metadata working
* [x] KV storage working
* [x] Secrets configured
* [x] Counter verified
* [x] Observability available
* [x] Documentation completed
