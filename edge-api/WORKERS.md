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


