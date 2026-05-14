# Setup steps (run once, then push)

## 1. Install Node.js
Download LTS from https://nodejs.org and install. Restart terminal after.

## 2. Create Cloudflare account
Go to https://dash.cloudflare.com/sign-up, confirm email.

## 3. Authenticate Wrangler
```powershell
cd lab17c\edge-api
npm install
npx wrangler login         # opens browser — click Allow
npx wrangler whoami        # should show your email
```

## 4. Create KV namespace
```powershell
npx wrangler kv namespace create SETTINGS
```
Copy the `id` from the output and paste it into `wrangler.jsonc`, replacing `PASTE_YOUR_KV_ID_HERE`.

## 5. Add secrets (type values when prompted)
```powershell
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```
Use any dummy values, e.g. `supersecret123` and your email.

## 6. Test locally
```powershell
npx wrangler dev
# open http://localhost:8787/health   — should return {"status":"ok"}
# open http://localhost:8787/edge     — cf metadata (may be null locally, that's fine)
# open http://localhost:8787/counter  — increments each refresh
```

## 7. Deploy (v1)
```powershell
npx wrangler deploy
```
Copy the printed `workers.dev` URL and update `WORKERS.md` line 5.

## 8. Test on real edge
```powershell
curl https://edge-api.<YOUR_SUBDOMAIN>.workers.dev/health
curl https://edge-api.<YOUR_SUBDOMAIN>.workers.dev/edge
curl https://edge-api.<YOUR_SUBDOMAIN>.workers.dev/counter
```

## 9. Deploy v2 (for deployment history)
Make a tiny change (e.g. add a field to `/` response), then:
```powershell
npx wrangler deploy
npx wrangler deployments list   # shows 2 versions
```

## 10. Screenshots to take
Put them in `lab17c/img/` (create the folder):
- `dashboard.png` — Cloudflare Workers dashboard showing your worker + request metrics
- `edge-response.png` — curl or browser output of `/edge` endpoint
- `logs.png` — `wrangler tail` terminal output OR dashboard logs tab

## 11. Update WORKERS.md
- Replace `<YOUR_SUBDOMAIN>` with your real subdomain on line 5
- Replace the example `/edge` JSON with your actual curl output
- Confirm the screenshots are in `lab17c/img/`

## 12. Commit and push
```powershell
cd c:\Users\lapin\PyCharmMiscProject\DevOps-CC
git add lab17c/
git commit -m "Add lab17: Cloudflare Workers edge API"
git push
```
