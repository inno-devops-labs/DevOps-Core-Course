# Edge API

Cloudflare Workers API for Lab 17.

## Routes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service metadata and route list |
| `GET` | `/health` | Health check |
| `GET` | `/edge` | Cloudflare request metadata |
| `GET` | `/counter` | KV-backed visits counter |
| `POST` | `/counter/reset` | Reset the visits counter |
| `GET` | `/config` | Plaintext vars and secret presence |

## Local Development

```bash
bun install
bun run dev
```

## Checks

```bash
bun run check
```

## Cloudflare Setup

Create the KV namespace and paste the returned IDs into `wrangler.jsonc`:

```bash
bunx wrangler kv namespace create SETTINGS
bunx wrangler kv namespace create SETTINGS --preview
```

Configure secrets without committing their values:

```bash
bunx wrangler secret put API_TOKEN
bunx wrangler secret put ADMIN_EMAIL
```

Deploy:

```bash
bunx wrangler deploy
```
