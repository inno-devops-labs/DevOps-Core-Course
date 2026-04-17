# edge-api — Cloudflare Worker (Lab 17)

TypeScript Worker deployed to Cloudflare's global edge. Full write-up
and comparison with Kubernetes live in the repo-root
[`WORKERS.md`](../WORKERS.md); this README is a quick-reference for
running the Worker locally.

## Files

| Path | Purpose |
|------|---------|
| `src/index.ts` | Worker source — routes `/`, `/health`, `/edge`, `/counter`, `/config`, `POST /admin/reset`. |
| `wrangler.jsonc` | Worker manifest (bundler target, `compatibility_date`, `vars`, KV binding). |
| `package.json` | `dev` / `deploy` / `tail` / `typecheck` scripts. |
| `tsconfig.json` | `strict: true`, Workers types enabled. |
| `.dev.vars.example` | Template for local-only secret values (copy to `.dev.vars`). |
| `evidence/` | Screenshots + CLI captures referenced from `WORKERS.md`. |

## Prerequisites

- Node.js ≥ 18 (local setup used v24).
- A Cloudflare account with Workers enabled. `workers.dev` subdomain
  works for this lab — no custom domain required.

## First-time setup

```bash
npm install

# 1. Authenticate wrangler. Opens a browser tab on your Cloudflare account.
npx wrangler login
npx wrangler whoami

# 2. Create the KV namespace (production + preview) and paste the IDs
#    into wrangler.jsonc → kv_namespaces[0].
npx wrangler kv namespace create SETTINGS
npx wrangler kv namespace create SETTINGS --preview

# 3. Set the runtime secrets (stored encrypted in Cloudflare, never in git).
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

## Local development

```bash
# Copy the local-dev secret template so `wrangler dev` has values.
cp .dev.vars.example .dev.vars

npm run dev        # wrangler dev — Miniflare-backed local edge on :8787

# In another terminal:
curl -s http://localhost:8787/health  | jq
curl -s http://localhost:8787/edge    | jq
curl -s http://localhost:8787/counter | jq
```

Under `wrangler dev` (without `--remote`), `request.cf` is
undefined — that's expected. Use the deployed Worker for real edge
metadata.

## Deploy

```bash
npm run deploy     # npx wrangler deploy

# Optional: live log tail while you curl the deployed URL
npm run tail       # npx wrangler tail
```

The deployed URL is printed at the end of `wrangler deploy` and has
the form `https://edge-api.<your-subdomain>.workers.dev`. For this
account it is <https://edge-api.e-torshin.workers.dev>.

> On the network used for this submission (RU residential), the
> single-command `npx wrangler deploy` finishes the bundle upload but
> fails the final trigger API call with `fetch failed` (`labs/lab17.md`
> explicitly warns about this for RU traffic). Use the two-step form
> instead — it is idempotent and reliably succeeds:
>
> ```bash
> npx wrangler versions upload
> npx wrangler triggers deploy
> ```

## Rollback

```bash
npx wrangler deployments list   # pick a previous version id
npx wrangler rollback           # interactive — confirms and rolls back
```

## Type check

```bash
npm run typecheck    # tsc --noEmit; strict mode is on
```
