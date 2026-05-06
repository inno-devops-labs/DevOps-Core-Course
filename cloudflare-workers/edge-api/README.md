# edge-api

Cloudflare Workers lab project for Lab 17.

## Routes

- `/` - app metadata
- `/health` - health check
- `/edge` - Cloudflare edge metadata
- `/counter` - Workers KV persisted counter
- `/config` - public config summary with secret-derived flags

## Required setup

1. Create a KV namespace named `SETTINGS`.
2. Replace `REPLACE_WITH_KV_NAMESPACE_ID` in `wrangler.jsonc`.
3. Create secrets:
   - `npx wrangler secret put API_TOKEN`
   - `npx wrangler secret put ADMIN_EMAIL`
4. Install dependencies and run locally:
   - `npm install`
   - `npm run dev`
5. Deploy:
   - `npm run deploy`

## Notes

- Plaintext vars live in `wrangler.jsonc`.
- Secrets are stored by Wrangler and are not committed.
- KV state persists across deployments.
