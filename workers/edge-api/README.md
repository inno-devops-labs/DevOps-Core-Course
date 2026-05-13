# edge-api (Cloudflare Workers)

Workers-native API used for Lab 17.

## Local setup

```bash
cd workers/edge-api
npm install
npx wrangler login
npx wrangler whoami
```

## Configure KV and secrets

Create KV namespace:

```bash
npx wrangler kv namespace create SETTINGS
```

Copy returned `id` into `wrangler.jsonc` (`kv_namespaces[0].id`).

Add secrets:

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

## Run and deploy

```bash
npx wrangler dev
npx wrangler deploy
```

## Routes

- `/` - app info
- `/health` - health check
- `/edge` - Cloudflare edge metadata
- `/counter` - KV-backed persisted counter
- `/config` - vars/secrets presence check (secret values hidden)
