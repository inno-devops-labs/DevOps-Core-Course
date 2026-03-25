# Lab 17 — Cloudflare Workers Edge Deployment

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Edge%20Computing-blue)
![points](https://img.shields.io/badge/points-20-orange)
![type](https://img.shields.io/badge/type-Exam%20Alternative-purple)

> Build and deploy a serverless HTTP API on Cloudflare's global edge network using Cloudflare Workers.

## Overview

Cloudflare Workers is a serverless edge platform for running code close to users worldwide without managing servers or choosing VM regions manually. Unlike Kubernetes or Docker-based PaaS platforms, Workers uses a lightweight runtime, automatic global distribution, built-in `workers.dev` URLs, and platform bindings for configuration, secrets, and state.

**This is an Exam Alternative Lab** — Complete both Lab 17 and Lab 18 to replace the final exam.

**What You'll Learn:**
- Edge computing concepts
- Serverless deployment workflows
- Cloudflare Workers and Wrangler CLI
- Global request metadata and routing
- Secrets, environment variables, and KV persistence
- Rollbacks and observability
- Kubernetes vs Workers trade-offs

**Prerequisites:**
- Git
- Node.js 18+ and npm
- Basic HTTP/JSON familiarity

**Important:** This lab does not deploy your Docker image from Lab 2. Cloudflare Workers is a serverless runtime, not a Docker host. You will build a Workers-native API that preserves similar operational concerns: routes, health checks, configuration, state, logs, deployments, and public access.

**Tech Stack:** Cloudflare Workers | Wrangler | TypeScript | Workers KV | `workers.dev`

---

## Exam Alternative Requirements

| Requirement | Details |
|-------------|---------|
| **Deadline** | 1 week before exam date |
| **Minimum Score** | 16/20 points |
| **Must Complete** | Both Lab 17 AND Lab 18 |
| **Total Points** | 40 pts (replaces 40 pt exam) |

---

## Tasks

### Task 1 — Cloudflare Setup (3 pts)

**Objective:** Set up your Cloudflare account and Workers tooling.

**Requirements:**

1. **Create Account**
   - Sign up for a Cloudflare account
   - Confirm you can access Workers from the dashboard
   - Understand what a `workers.dev` subdomain is

2. **Create Project**
   - Create a new Workers project using C3 (`create-cloudflare`)
   - Choose the `Worker only` template
   - Use TypeScript for the required path in this lab

3. **Authenticate CLI**
   - Log in with Wrangler
   - Verify your account with `npx wrangler whoami`
   - Understand the role of `wrangler.jsonc`

4. **Explore Platform Concepts**
   - Understand the Workers runtime
   - Understand `workers.dev` URLs
   - Understand bindings: vars, secrets, and KV namespaces

<details>
<summary>💡 Hints</summary>

**Create the project:**
```bash
npm create cloudflare@latest -- edge-api
cd edge-api
```

**Recommended choices during setup:**
- Hello World example
- Worker only
- TypeScript
- Git: Yes
- Deploy now: No

**Authenticate:**
```bash
npx wrangler login
npx wrangler whoami
```

**What to look for in the generated project:**
- `src/index.ts` - Worker source code
- `wrangler.jsonc` - Worker configuration
- `package.json` - local scripts and dependencies

**Resources:**
- [Cloudflare Workers Overview](https://developers.cloudflare.com/workers/)
- [Get started with Wrangler](https://developers.cloudflare.com/workers/get-started/guide/)
- [Wrangler commands](https://developers.cloudflare.com/workers/wrangler/commands/)

</details>

---

### Task 2 — Build and Deploy a Worker API (4 pts)

**Objective:** Build a small HTTP API and deploy it to Cloudflare's edge.

**Requirements:**

1. **Implement Routes**
   - Create at least 3 HTTP endpoints
   - Include `/health`
   - Include one endpoint that returns JSON metadata about the deployment

2. **Run Locally**
   - Start local development with `npx wrangler dev`
   - Test routes in the browser or with `curl`
   - Verify correct status codes and JSON responses

3. **Deploy**
   - Deploy with `npx wrangler deploy`
   - Access the public `workers.dev` URL
   - Confirm the deployed Worker responds correctly

4. **Use Versioned Source Control**
   - Commit your Worker project to Git
   - Keep a clean deployment history you can refer to later

<details>
<summary>💡 Hints</summary>

**Example route set:**
- `/` - general app information
- `/health` - health status
- `/edge` - edge metadata
- `/counter` - KV-backed persisted counter

**Minimal TypeScript example:**
```ts
export interface Env {
  APP_NAME: string;
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

    return new Response("Not Found", { status: 404 });
  },
};
```

**Local development:**
```bash
npx wrangler dev
```

**Deploy:**
```bash
npx wrangler deploy
```

**Expected public URL format:**
```text
https://<worker-name>.<your-subdomain>.workers.dev
```

</details>

---

### Task 3 — Global Edge Behavior (4 pts)

**Objective:** Inspect how your Worker behaves on Cloudflare's global network.

**Requirements:**

1. **Add Edge Metadata Endpoint**
   - Return information from the incoming request context
   - Include at least `colo` and `country`
   - Include at least 1 additional field such as `asn`, `city`, `httpProtocol`, or `tlsVersion`

2. **Verify Public Edge Execution**
   - Call your deployed Worker using the public URL
   - Capture the JSON response from the metadata endpoint
   - Show evidence that Cloudflare provides request metadata at the edge

3. **Explain Global Distribution**
   - Briefly explain how Workers distributes execution globally
   - Compare this with manually choosing regions in VM or PaaS platforms
   - Explain why there is no `deploy to 3 regions` step in Workers

4. **Document Routing Concepts**
   - Explain the difference between `workers.dev`, Routes, and Custom Domains
   - Use `workers.dev` for the required deployment
   - Custom domain setup is optional

<details>
<summary>💡 Hints</summary>

**Useful request metadata:**
```ts
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
```

**Test with `curl`:**
```bash
curl https://<worker-name>.<your-subdomain>.workers.dev/edge
```

**Routing concepts:**
- `workers.dev` gives you a public URL quickly
- Routes attach Workers to traffic for an existing Cloudflare zone
- Custom Domains make your Worker the origin for a domain or subdomain

**Resources:**
- [Request API and `request.cf`](https://developers.cloudflare.com/workers/runtime-apis/request/)
- [How Workers works](https://developers.cloudflare.com/workers/reference/how-workers-works/)
- [`workers.dev` routing](https://developers.cloudflare.com/workers/configuration/routing/workers-dev/)
- [Routes and domains](https://developers.cloudflare.com/workers/configuration/routing/)

</details>

---

### Task 4 — Configuration, Secrets & Persistence (3 pts)

**Objective:** Configure your Worker with variables, secrets, and persistent state.

**Requirements:**

1. **Add Environment Variables**
   - Define at least 1 plaintext variable in `wrangler.jsonc`
   - Use it in your Worker response
   - Explain why plaintext vars are not suitable for secrets

2. **Add Secrets**
   - Create at least 2 secrets with Wrangler
   - Use the values through the `env` object
   - Do not commit secret values to Git

3. **Add Persistence with Workers KV**
   - Create a KV namespace
   - Bind it to your Worker
   - Store and retrieve at least 1 value through your API

4. **Verify Persistence**
   - Confirm the stored value still exists after a redeploy
   - Document what you stored and how you verified it

<details>
<summary>💡 Hints</summary>

**Plaintext vars in `wrangler.jsonc`:**
```json
{
  "vars": {
    "APP_NAME": "edge-api",
    "COURSE_NAME": "devops-core"
  }
}
```

**Secrets:**
```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

**Create KV namespace:**
```bash
npx wrangler kv namespace create SETTINGS
```

Add the returned namespace ID to `wrangler.jsonc`:
```json
{
  "kv_namespaces": [
    {
      "binding": "SETTINGS",
      "id": "<your-namespace-id>"
    }
  ]
}
```

**Example KV-backed counter:**
```ts
export interface Env {
  APP_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

if (url.pathname === "/counter") {
  const raw = await env.SETTINGS.get("visits");
  const visits = Number(raw ?? "0") + 1;
  await env.SETTINGS.put("visits", String(visits));
  return Response.json({ visits });
}
```

**Resources:**
- [Environment variables](https://developers.cloudflare.com/workers/configuration/environment-variables/)
- [Secrets](https://developers.cloudflare.com/workers/configuration/secrets/)
- [Workers KV getting started](https://developers.cloudflare.com/kv/get-started/)
- [Workers KV pricing](https://developers.cloudflare.com/kv/platform/pricing/)

</details>

---

### Task 5 — Observability & Operations (3 pts)

**Objective:** Observe your Worker in production and manage deployments.

**Requirements:**

1. **Inspect Logs**
   - Add at least 1 `console.log()` statement
   - View logs with `npx wrangler tail` or in the dashboard
   - Capture an example log entry

2. **Inspect Metrics**
   - Open the Worker in the Cloudflare dashboard
   - Review request counts, errors, or execution metrics
   - Briefly explain what metric you looked at

3. **Manage Deployments**
   - Deploy at least 2 versions of your Worker
   - View deployment history
   - Perform or describe a rollback to a previous version

<details>
<summary>💡 Hints</summary>

**Console logging example:**
```ts
console.log("path", url.pathname, "colo", request.cf?.colo);
```

**Tail logs from the terminal:**
```bash
npx wrangler tail
```

**View deployments:**
```bash
npx wrangler deployments list
```

**Rollback:**
```bash
npx wrangler rollback
```

**Resources:**
- [Observability overview](https://developers.cloudflare.com/workers/observability/)
- [Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/)
- [Versions & Deployments](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/)
- [Rollbacks](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/)

</details>

---

### Task 6 — Documentation & Comparison (3 pts)

**Objective:** Document your deployment and compare Workers with Kubernetes.

**Create `WORKERS.md` with:**

1. **Deployment Summary**
   - Worker URL
   - Main routes
   - Configuration used

2. **Evidence**
   - Screenshot of Cloudflare dashboard
   - Example `/edge` JSON response
   - Example log or metrics screenshot

3. **Kubernetes vs Cloudflare Workers Comparison**

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| Setup complexity | | |
| Deployment speed | | |
| Global distribution | | |
| Cost (for small apps) | | |
| State/persistence model | | |
| Control/flexibility | | |
| Best use case | | |

4. **When to Use Each**
   - Scenarios favoring Kubernetes
   - Scenarios favoring Workers
   - Your recommendation

5. **Reflection**
   - What felt easier than Kubernetes?
   - What felt more constrained?
   - What changed because Workers is not a Docker host?

---

## Checklist

- [ ] Cloudflare account created
- [ ] Workers project initialized
- [ ] Wrangler authenticated
- [ ] Worker deployed to `workers.dev`
- [ ] `/health` endpoint working
- [ ] Edge metadata endpoint implemented
- [ ] At least 1 plaintext variable configured
- [ ] At least 2 secrets configured
- [ ] KV namespace created and bound
- [ ] Persistence verified after redeploy
- [ ] Logs or metrics reviewed
- [ ] Deployment history viewed
- [ ] `WORKERS.md` documentation complete
- [ ] Kubernetes comparison documented

---

## Rubric

| Criteria | Points |
|----------|--------|
| **Setup** | 3 pts |
| **Worker API** | 4 pts |
| **Edge Behavior** | 4 pts |
| **Configuration & Persistence** | 3 pts |
| **Operations** | 3 pts |
| **Documentation** | 3 pts |
| **Total** | **20 pts** |

**Grading:**
- **18-20:** Excellent deployment, strong edge analysis, thorough comparison
- **16-17:** Working Worker, good documentation, minor gaps
- **14-15:** Basic deployment works, missing KV, observability, or analysis detail
- **<14:** Incomplete implementation

---

## Resources

<details>
<summary>📚 Core Cloudflare Workers Docs</summary>

- [Cloudflare Workers Overview](https://developers.cloudflare.com/workers/)
- [Get started with Wrangler](https://developers.cloudflare.com/workers/get-started/guide/)
- [Wrangler commands](https://developers.cloudflare.com/workers/wrangler/commands/)
- [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/)

</details>

<details>
<summary>🌍 Edge Runtime & Routing</summary>

- [How Workers works](https://developers.cloudflare.com/workers/reference/how-workers-works/)
- [Request API and `request.cf`](https://developers.cloudflare.com/workers/runtime-apis/request/)
- [`workers.dev`](https://developers.cloudflare.com/workers/configuration/routing/workers-dev/)
- [Routes and domains](https://developers.cloudflare.com/workers/configuration/routing/)
- [Custom Domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/)

</details>

<details>
<summary>🔐 Config, Secrets & State</summary>

- [Environment variables](https://developers.cloudflare.com/workers/configuration/environment-variables/)
- [Secrets](https://developers.cloudflare.com/workers/configuration/secrets/)
- [Workers KV getting started](https://developers.cloudflare.com/kv/get-started/)
- [Workers KV pricing](https://developers.cloudflare.com/kv/platform/pricing/)

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

- [Python Workers](https://developers.cloudflare.com/workers/languages/python/)
- [Python Worker packages](https://developers.cloudflare.com/workers/languages/python/packages/)

</details>

---

**Good luck!** 🌍

> **Remember:** Cloudflare Workers is excellent for globally distributed APIs and lightweight edge logic. Kubernetes gives you more control, broader runtime flexibility, and stronger patterns for long-running container workloads. Choose the right model for the workload.
