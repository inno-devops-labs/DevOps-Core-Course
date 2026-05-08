# edge-api

Cloudflare Workers HTTP API for DevOps Lab 17. TypeScript Worker with KV persistence, plaintext vars, and secrets.

## Endpoints

| Path | Description |
|------|-------------|
| `/` | Service info, version, environment, available endpoints |
| `/health` | Liveness check `{status, timestamp}` |
| `/edge` | Edge metadata from `request.cf` (colo, country, city, asn, httpProtocol, tlsVersion) |
| `/counter` | KV-backed visit counter (increments per call) |
| `/config` | Surfaces plaintext vars and confirms secret/KV bindings (no secret values) |

## Quick Start

```bash
cd labs-work/edge-api
npm install
npx wrangler login
npx wrangler dev
```

In another terminal:

```bash
curl http://localhost:8787/
curl http://localhost:8787/health
curl http://localhost:8787/edge
curl http://localhost:8787/counter
curl http://localhost:8787/config
```

## Deploy

Before the first deploy, create a KV namespace and replace the placeholder ID in `wrangler.jsonc`:

```bash
npx wrangler kv namespace create SETTINGS
```

Add secrets (values are not committed):

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

Deploy and exercise the public URL:

```bash
npx wrangler deploy
WORKER_URL=https://edge-api.<your-subdomain>.workers.dev
curl $WORKER_URL/health
curl $WORKER_URL/edge
```

## Local Secrets

For `wrangler dev`, place secret values in `.dev.vars` (gitignored):

```text
API_TOKEN=local-dev-token
ADMIN_EMAIL=dev@example.com
```

## Operations

```bash
npx wrangler tail               # live logs
npx wrangler deployments list   # deployment history
npx wrangler rollback           # revert to a previous version
```

## Project Layout

```
edge-api/
├── src/
│   └── index.ts        # Worker entrypoint and routes
├── wrangler.jsonc      # Worker config (vars, KV bindings, observability)
├── package.json        # npm scripts and Wrangler dependency
├── tsconfig.json       # TypeScript compiler config
└── .gitignore
```

See `WORKERS.md` for the full lab writeup, evidence, and the Kubernetes vs Workers comparison.
