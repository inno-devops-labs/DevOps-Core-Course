# Evidence — Lab 17 (Cloudflare Workers)

Store screenshots and raw CLI captures here. Filenames are referenced
from [`../../WORKERS.md`](../../WORKERS.md); keep them stable so the
evidence table keeps rendering.

| File | Produced by | What it must show | Task |
|------|-------------|-------------------|------|
| `01-wrangler-whoami.txt` | `npx wrangler whoami` | Logged-in account email + accessible accounts list. | 1 |
| `02-kv-namespace-create.txt` | `npx wrangler kv namespace create SETTINGS` (and `--preview`) | Returned namespace IDs that were pasted into `wrangler.jsonc`. | 4 |
| `03-wrangler-deploy.txt` | `npx wrangler deploy` tail | Upload size, bindings list, published workers.dev URL. | 2 |
| `04-curl-health.txt` | `curl -i https://edge-api.e-torshin.workers.dev/health` | `HTTP/2 200` + JSON body with `status: "ok"`. | 2 |
| `05-curl-edge.json` | `curl https://edge-api.e-torshin.workers.dev/edge` | Real `colo` / `country` / `asn` / `httpProtocol` fields populated by Cloudflare's edge. | 3 |
| `06-curl-config.json` | `curl https://edge-api.e-torshin.workers.dev/config` | Plaintext var values + `"secrets.API_TOKEN": "set"` + `"bindings.SETTINGS": "bound"`. | 4 |
| `07-secrets-list.txt` | `npx wrangler secret list` | Secret *names* only (Cloudflare never returns values). | 4 |
| `08-kv-persist.txt` | `curl .../counter` before and after `wrangler deploy` | Counter survives a redeploy — proves KV is persistence, not memory. | 4 |
| `09-tail.txt` | `npx wrangler tail` session with 2–3 requests routed through | Structured JSON log lines emitted from `src/index.ts`. | 5 |
| `10-deployments-list.txt` | `npx wrangler deployments list` | ≥2 versions with timestamps + author. | 5 |
| `11-rollback.txt` | `npx wrangler rollback` (interactive) | Prompt + confirmation of the previous version going live. | 5 |
| `12-dashboard-metrics.png` | Cloudflare dashboard → Workers & Pages → `edge-api` → Metrics | Requests/min, success rate, CPU time; any non-zero window. | 5 |
| `13-dashboard-overview.png` | Cloudflare dashboard → Workers & Pages → `edge-api` | Worker overview page with the workers.dev URL visible. | 6 |

Rule of thumb: **every claim in `WORKERS.md` points to a file here.**
Graders follow the links, so missing evidence = missing points.

## How to capture these from a shell

```bash
cd edge-api
npx wrangler whoami            > evidence/01-wrangler-whoami.txt 2>&1
npx wrangler deploy            > evidence/03-wrangler-deploy.txt 2>&1

URL="https://edge-api.e-torshin.workers.dev"
curl -is  "$URL/health"        > evidence/04-curl-health.txt
curl -sS  "$URL/edge"   | tee  evidence/05-curl-edge.json
curl -sS  "$URL/config" | tee  evidence/06-curl-config.json

npx wrangler secret list       > evidence/07-secrets-list.txt 2>&1
npx wrangler deployments list  > evidence/10-deployments-list.txt 2>&1
```

For the KV persistence capture (`08-kv-persist.txt`):

```bash
{
  echo "# before redeploy"
  curl -sS "$URL/counter"
  npx wrangler deploy >/dev/null 2>&1
  echo "# after redeploy"
  curl -sS "$URL/counter"
} > evidence/08-kv-persist.txt
```
