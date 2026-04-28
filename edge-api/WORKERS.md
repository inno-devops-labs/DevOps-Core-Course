# Lab 17 — Cloudflare Workers Edge Deployment

# Task 1 — Cloudflare Setup

## 1.1 Objective

The goal of this task was to set up a Cloudflare Workers project, authenticate Wrangler CLI, and understand the basic Workers platform concepts.

## 1.2 Local Tooling

The local environment was checked before creating the Worker project.

Commands:

```bash
node --version
npm --version
git --version
npx wrangler --version
```

Output:

```text
v23.11.0
10.9.2
git version 2.48.1

wrangler 4.86.0
```

Node.js, npm, Git, and Wrangler were available locally.

## 1.3 Cloudflare Account and Dashboard

A Cloudflare account was used for this lab.

Wrangler authentication was completed successfully with:

```bash
npx wrangler login
```

Output:

```text
Successfully logged in.
```

The Workers & Pages dashboard is used to manage Workers, view deployments, inspect metrics, configure bindings, and review logs.

## 1.4 workers.dev Subdomain

A `workers.dev` subdomain provides a public URL for Cloudflare Workers without requiring a custom domain.

Expected public URL format:

```text
https://<worker-name>.<your-subdomain>.workers.dev
```

This lab uses the `workers.dev` URL for the required public deployment.

## 1.5 Project Creation

The Worker project was created with C3:

```bash
npm create cloudflare@latest -- edge-api
```

Selected setup:

```text
Worker name: edge-api
Template: Hello World
Type: Worker only
Language: TypeScript
Deploy now: No
```

Project creation completed successfully:

```text
SUCCESS Application created successfully!
```

The project directory is:

```text
edge-api
```

Important generated files:

```text
edge-api/src/index.ts
edge-api/wrangler.jsonc
edge-api/package.json
edge-api/tsconfig.json
edge-api/package-lock.json
```

## 1.6 Project Structure

The generated project was checked with:

```bash
ls -la
find . -maxdepth 2 -type f | sort
```

Important files:

```text
./package.json
./src/index.ts
./tsconfig.json
./wrangler.jsonc
./package-lock.json
./test/index.spec.ts
```

## 1.7 package.json Scripts

The generated `package.json` contains Wrangler scripts:

```json
{
  "scripts": {
    "deploy": "wrangler deploy",
    "dev": "wrangler dev",
    "start": "wrangler dev",
    "test": "vitest",
    "cf-typegen": "wrangler types"
  }
}
```

These scripts are used for local development, deployment, testing, and Cloudflare type generation.

## 1.8 Wrangler Authentication Verification

Wrangler account verification command:

```bash
npx wrangler whoami
```

Output:

```bash
Getting User settings...
You are logged in with an OAuth Token, associated with the email <email>.

Account Name: <account-name>
Account ID: 2a703...aaa

Token Permissions:
- account (read)
- user (read)
- workers (write)
- workers_kv (write)
- workers_routes (write)
- workers_scripts (write)
- workers_tail (read)
- offline_access
```

This confirms that the local Wrangler CLI is authenticated with the Cloudflare account.


## 1.9 wrangler.jsonc

The `wrangler.jsonc` file is the main configuration file for the Worker.

Current important fields:

```jsonc
{
  "name": "edge-api",
  "main": "src/index.ts",
  "compatibility_date": "2026-04-28",
  "observability": {
    "enabled": true
  },
  "upload_source_maps": true,
  "compatibility_flags": [
    "nodejs_compat"
  ]
}
```

The role of `wrangler.jsonc`:

* defines the Worker name
* defines the source entrypoint
* sets the compatibility date
* enables observability options
* later stores plaintext variables
* later stores bindings such as KV namespaces

Secret values should not be committed to `wrangler.jsonc`. Secrets are managed separately with Wrangler.

## 1.10 Local Development Test

The Worker was started locally with:

```bash
npm run dev
```

Output:

```text
Ready on http://localhost:8787
GET / 200 OK
```

The local endpoint was tested with:

```bash
curl -i http://localhost:8787
```

Output:

```text
HTTP/1.1 200 OK
Content-Type: text/plain;charset=UTF-8

Hello World!
```

This confirms that the generated Worker runs locally.

## 1.11 Platform Concepts

Cloudflare Workers run code on Cloudflare's serverless edge runtime instead of a traditional server, VM, container, or Kubernetes cluster.

Important concepts:

* Workers runtime: lightweight serverless runtime for handling HTTP requests
* `workers.dev`: built-in public domain for deployed Workers
* vars: plaintext environment variables configured in `wrangler.jsonc`
* secrets: sensitive values created with Wrangler and exposed through `env`
* KV namespaces: globally available key-value storage that can be bound to a Worker

---

# Task 2 — Build and Deploy a Worker API

## 2.1 Objective

The goal of this task was to build a small HTTP JSON API with Cloudflare Workers, run it locally, deploy it to Cloudflare, and verify the public `workers.dev` URL.

## 2.2 Implemented Routes

The default Hello World Worker was replaced with a TypeScript API in:

```text
edge-api/src/index.ts
```

Implemented endpoints:

* `/` — general service information
* `/health` — health check endpoint
* `/deployment` — deployment metadata endpoint
* `/edge` — edge metadata endpoint

Error handling was also added:

* unknown routes return `404 Not Found`
* unsupported methods return `405 Method Not Allowed`

## 2.3 Local Development Verification

The Worker was started locally with:

```bash
npm run dev
```

Output:

```text
Ready on http://localhost:8787
```

Local routes were tested with `curl`.

Health endpoint:

```bash
curl -i http://localhost:8787/health
```

Output:

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{"status":"healthy","service":"edge-api","timestamp":"2026-04-28T13:35:26.566Z"}
```

Deployment metadata endpoint:

```bash
curl -i http://localhost:8787/deployment
```

Output:

```text
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{"application":"edge-api","platform":"Cloudflare Workers","language":"TypeScript","environment":"workers.dev","version":"lab17-task2","deployedWith":"Wrangler","publicUrlFormat":"https://<worker-name>.<subdomain>.workers.dev","timestamp":"2026-04-28T13:35:30.264Z"}
```

Edge endpoint:

```bash
curl -s http://localhost:8787/edge | python3 -m json.tool
```

Output:

```json
{
    "colo": "RIX",
    "country": "LV",
    "city": "Riga",
    "asn": 43513,
    "httpProtocol": "HTTP/1.1",
    "tlsVersion": "TLSv1.3",
    "note": "Cloudflare edge metadata is available after deployment.",
    "timestamp": "2026-04-28T13:35:56.376Z"
}
```

Error responses were verified:

```bash
curl -i http://localhost:8787/not-found
curl -i -X POST http://localhost:8787/health
```

Results:

```text
/not-found       -> 404 Not Found
POST /health     -> 405 Method Not Allowed
```

## 2.4 Tests

The tests were updated to match the new JSON API.

Command:

```bash
npm test -- --run
```

Output:

```text
✓ test/index.spec.ts (5 tests) 39ms

Test Files  1 passed (1)
Tests       5 passed (5)
```

## 2.5 Deployment

The Worker was deployed with Wrangler:

```bash
npx wrangler deploy
```

Output:

```text
Uploaded edge-api
Deployed edge-api triggers
https://edge-api.<user-name>.workers.dev
Current Version ID: 60c067a3-3760-45dd-a583-eaf71e3ff60f
```

Public Worker URL:

```text
https://edge-api.<user-name>.workers.dev
```

## 2.6 Public URL Verification

The deployed Worker was tested through the public `workers.dev` URL:

```bash
WORKER_URL="https://edge-api.<user-name>.workers.dev"

curl -i "$WORKER_URL/"
curl -i "$WORKER_URL/health"
curl -i "$WORKER_URL/deployment"
curl -i "$WORKER_URL/edge"
curl -i "$WORKER_URL/not-found"
```

Results:

```text
/              -> HTTP/2 200
/health        -> HTTP/2 200
/deployment    -> HTTP/2 200
/edge          -> HTTP/2 200
/not-found     -> HTTP/2 404
```

Example deployed `/edge` response:

```json
{
    "colo": "RIX",
    "country": "LV",
    "city": "Riga",
    "asn": 43513,
    "httpProtocol": "HTTP/2",
    "tlsVersion": "TLSv1.3",
    "note": "Cloudflare edge metadata is available after deployment.",
    "timestamp": "2026-04-28T13:38:29.382Z"
}
```

## 2.7 Source Control

The Worker project was committed to Git:

```bash
git add edge-api/.
git commit -m "feat: add Cloudflare Workers API"
```

Output:

```text
[lab17 906c207] feat: add Cloudflare Workers API
```

---


# Task 3 — Global Edge Behavior

## 3.1 Objective

The goal of this task was to inspect how the deployed Worker behaves on Cloudflare's global edge network and verify that Cloudflare provides request metadata at runtime.

## 3.2 Edge Metadata Endpoint

The Worker includes an `/edge` endpoint that reads metadata from the incoming request context.

Implemented fields:

- `colo`
- `country`
- `city`
- `asn`
- `httpProtocol`
- `tlsVersion`

Code check:

```bash
grep -A15 'url.pathname === "/edge"' src/index.ts
```

Important implementation:

```ts
if (url.pathname === "/edge") {
	return jsonResponse({
		colo: request.cf?.colo ?? "local-dev",
		country: request.cf?.country ?? "local-dev",
		city: request.cf?.city ?? "local-dev",
		asn: request.cf?.asn ?? "local-dev",
		httpProtocol: request.cf?.httpProtocol ?? "local-dev",
		tlsVersion: request.cf?.tlsVersion ?? "local-dev",
		note: "Cloudflare edge metadata is available after deployment.",
		timestamp,
	});
}
```

## 3.3 Public Edge Verification

The deployed Worker was called through the public `workers.dev` URL:

```bash
WORKER_URL="https://edge-api.<user-name>.workers.dev"

curl -s "$WORKER_URL/edge" | python3 -m json.tool
```

Output:

```json
{
    "colo": "HEL",
    "country": "FI",
    "city": "Helsinki",
    "asn": 215730,
    "httpProtocol": "HTTP/2",
    "tlsVersion": "TLSv1.3",
    "note": "Cloudflare edge metadata is available after deployment.",
    "timestamp": "2026-04-28T17:33:03.176Z"
}
```

This confirms that the Worker executed on Cloudflare's edge network and received Cloudflare-provided request metadata.

## 3.4 Header Verification

The deployed endpoint was also checked with response headers:

```bash
curl -i "$WORKER_URL/edge"
```

Important output:

```text
HTTP/2 200
server: cloudflare
cf-ray: 9f37cf7feec38ddb-HEL
```

The `server: cloudflare` header confirms that the response was served through Cloudflare. The `cf-ray` suffix `HEL` matches the Cloudflare edge location.

## 3.5 Global Distribution Explanation

Cloudflare Workers run on Cloudflare's global edge network. After deployment, the Worker is available globally without manually choosing VM regions or provisioning regional infrastructure.

In a VM, Kubernetes, or traditional PaaS setup, global deployment usually requires:

* choosing target regions
* deploying infrastructure in each region
* configuring load balancing
* managing regional failover

With Cloudflare Workers, there is no separate `deploy to 3 regions` step. The Worker is deployed to Cloudflare's platform, and Cloudflare automatically routes requests to an appropriate nearby edge location.

## 3.6 Routing Concepts

Cloudflare Workers can be exposed in several ways.

### workers.dev

`workers.dev` provides a built-in public URL for a Worker without requiring a custom domain.

Used in this lab:

```text
https://edge-api.<user-name>.workers.dev
```

### Routes

Routes attach a Worker to traffic for an existing Cloudflare-managed zone.

Example:

```text
example.com/api/*
```

This is useful when only specific paths on an existing domain should be handled by a Worker.

### Custom Domains

Custom Domains expose a Worker directly on a custom hostname.

Example:

```text
api.example.com
```

This is useful for production APIs, but it was not required for this lab.

---


