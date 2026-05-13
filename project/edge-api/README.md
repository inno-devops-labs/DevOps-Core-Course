# edge-api

Cloudflare Workers edge API for **DevOps Core Course Lab 17**.

Lab spec: [`labs/lab17.md`](../../labs/lab17.md). Operator runbook + evidence: [`WORKERS.md`](WORKERS.md). Lab report: [`docs/LAB17.md`](../docs/LAB17.md).

## Routes

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | App info, plaintext vars, version, route list |
| GET | `/health` | Health check + cold-start uptime |
| GET | `/edge` | `request.cf` metadata (colo, country, city, asn, httpProtocol, tlsVersion, region) |
| GET | `/counter` | Workers KV-backed visit counter (binding: `SETTINGS`, key: `visits`) |
| GET | `/secret-check` | Reports `API_TOKEN` / `ADMIN_EMAIL` presence (length only — values never leak) |

## Run locally

```bash
npm install
cp .dev.vars.example .dev.vars   # then put any local values for the two secrets
npx wrangler dev                  # http://localhost:8787
```

## Deploy

```bash
npx wrangler login
npx wrangler kv namespace create SETTINGS   # paste the id into wrangler.jsonc
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
npx wrangler deploy
```

Full step-by-step walkthrough with expected outputs is in [`WORKERS.md`](WORKERS.md) §2.
