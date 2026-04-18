# Evidence — Lab 18 (IPFS + 4EVERLAND)

Raw captures referenced from
[`../../../4EVERLAND.md`](../../../4EVERLAND.md) and
[`../README.md`](../README.md). Keep filenames stable so the evidence
tables keep rendering.

## Auto-generated (local Kubo node)

These are produced by
[`../scripts/collect-ipfs-evidence.sh`](../scripts/collect-ipfs-evidence.sh)
and are fully reproducible — the CIDs are deterministic.

| File | Produced by | What it must show | Task |
|------|-------------|-------------------|------|
| `01-ipfs-version.txt` | `ipfs --version` | Kubo version inside the container (0.30.0 here). | 1 |
| `02-ipfs-id.json` | `ipfs id` | PeerID, multiaddrs, protocol list. | 1 |
| `02b-ipfs-config-summary.json` | `ipfs config show \| jq` | API / Gateway / Swarm endpoint config. | 1 |
| `03-ipfs-add-hello.txt` | `ipfs add /tmp/hello.txt` | One line: `added <CID> hello.txt`. | 1 |
| `04-ipfs-gateway-hello.txt` | `curl http://127.0.0.1:8080/ipfs/<CID>` | Gateway serves the exact bytes that were added. | 1 |
| `05-ipfs-pin-ls.txt` | `ipfs pin ls --type=recursive` | The hello-CID is pinned (so GC can't drop it). | 1 |
| `06-ipfs-add-site.txt` | `ipfs add -r --cid-version=1 /site` | File-CID + directory-CID for the landing page. | 3 |
| `07-ipfs-gateway-site.txt` | `curl http://127.0.0.1:8080/ipfs/<DirCID>/index.html` | `HTTP 200`, body starts with `<!DOCTYPE html>`. | 3 |
| `08-cid-deterministic.txt` | Three `ipfs add --only-hash` calls | Same input → same CID; 1-byte diff → different CID. | 1 |
| `09-cid-mutability-v2.txt` | `ipfs add -r` on two versions of the site | New content ⇒ new directory CID (motivates IPNS / Task 5). | 5 |
| `10-ipfs-stats.txt` | `ipfs repo stat` / `stats bw` / `swarm peers` / `dag stat` | Repo size, swarm peer count, DAG block count. | 1 |
| `11-public-gateway-check.txt` | `curl` against ipfs.io / dweb.link / 4everland.link | Local-only pins aren't always reachable externally — that's *why* pinning services exist. | 4 |
| `12-webui-reachable.txt` | `curl /webui` + `POST /api/v0/version` | HTTP 301 → `/webui/` + RPC API responds with Kubo version. | 1 |

## Manual (after the 4EVERLAND deploy)

Capture these from the real 4EVERLAND dashboard **after** completing
the web-UI flow described in
[`../../../4EVERLAND.md`](../../../4EVERLAND.md) §3–§5. Filenames are
what that document links to.

| File | How to capture | What it must show | Task |
|------|----------------|-------------------|------|
| `13-4everland-hosting-project.png` | Dashboard → Hosting → your project overview | Project name, platform URL, latest deployment status **Ready**. | 3 |
| `14-4everland-deployment-detail.png` | Click the latest deployment | Commit SHA, build log tail, **IPFS CID** column populated. | 3 |
| `15-site-via-4everland-app.png` | Load `https://<slug>.4everland.app` in a browser | Landing page renders; DevTools network tab on the HTML response. | 3 |
| `16-site-via-ipfs-4everland-link.png` | Load `https://ipfs.4everland.link/ipfs/<CID>/` | Same page via the IPFS gateway, path shows the CID. | 3 |
| `17-4everland-bucket-contents.png` | Dashboard → Bucket → your bucket | Uploaded files with sizes and individual CIDs. | 4 |
| `18-bucket-directory-cid.png` | Upload the `lab18-site` folder | Directory entry with a directory-CID (`bafybei…`). | 4 |
| `19-public-gateway-grid.png` | Open `/ipfs/<CID>` on ipfs.io, dweb.link, cloudflare-ipfs.com, 4everland.link in four tabs | Same CID renders the same page everywhere. | 4 |
| `20-public-gateways-after-pin.txt` | `curl` loop from `../README.md` | All four gateways return `200` in <5 s once the CID is pinned on 4EVERLAND. | 4 |
| `21-4everland-domains.png` | Dashboard → Hosting → Domains | Project auto-subdomain + (optional) custom domain panel. | 5 |
| `22-redeploy-new-cid.png` | Push a small edit, wait for rebuild, open Deployments tab | Two entries: old-CID → new-CID, same URL. | 5 |

Rule of thumb: **every claim in `4EVERLAND.md` points to a file here.**
If you change the page and push, refresh 22 so the "two different CIDs
behind the same URL" story stays honest.

## One-shot refresh

```bash
cd ipfs-site
docker compose up -d && sleep 10
./scripts/collect-ipfs-evidence.sh
```

The 4EVERLAND screenshots (13–22) are manual — they live behind your
account's login and can't be captured by the script.
