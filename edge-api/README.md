# edge-api

Cloudflare Worker for Lab 17. The full lab report is in [`WORKERS.md`](WORKERS.md).

The Worker is a small Hono API with Cloudflare edge metadata, redacted configuration inspection, and a KV-backed counter.

## Commands

```bash
npm install
npm run typecheck
npx wrangler types
npx wrangler dev --port 8787
npx wrangler deploy
```

## Routes

- `GET /`
- `GET /health`
- `GET /edge`
- `GET /config`
- `GET /counter`
- `POST /counter`
