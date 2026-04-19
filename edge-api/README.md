# Edge API

Cloudflare Workers project for Lab 17.

## Local setup

```bash
cd edge-api
npm install
cp .dev.vars.example .dev.vars
npx wrangler dev
```

## Routes

- `GET /`
- `GET /health`
- `GET /edge`
- `GET /config`
- `GET /counter`
- `GET /kv?key=...`
- `POST /kv`

## Cloudflare setup

```bash
npx wrangler login
npx wrangler whoami
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
npx wrangler kv namespace create SETTINGS
npx wrangler kv namespace create SETTINGS --preview
```

Update `wrangler.jsonc` with the returned KV namespace IDs before deploying.
