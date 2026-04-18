# Lab 18 — Deployable Artifact

This directory is the **content root** published to IPFS / 4EVERLAND.
The main lab write-up lives at [`../../4EVERLAND.md`](../../4EVERLAND.md);
this README is the "what's in the box" for the deployable itself.

```
ipfs-site/
├── README.md               ← this file
├── index.html              ← the static site that gets pinned
├── docker-compose.yml      ← one-command local Kubo node (Task 1)
├── scripts/
│   └── collect-ipfs-evidence.sh   ← reproduces everything under evidence/
└── evidence/
    ├── README.md           ← map of evidence files ↔ lab tasks
    ├── 01..12*.txt / .json ← CLI captures (auto-generated, idempotent)
    └── *.png               ← 4EVERLAND dashboard screenshots (manual)
```

## Quick reproduce (local IPFS node — Task 1)

```bash
cd ipfs-site
docker compose up -d
# wait ~10s for Kubo to initialise, then:
./scripts/collect-ipfs-evidence.sh
```

The script is idempotent: running it twice yields byte-identical CIDs
(that's literally what content addressing guarantees — see
[`evidence/08-cid-deterministic.txt`](./evidence/08-cid-deterministic.txt)).

Teardown:

```bash
docker compose down -v   # also wipes the pinned blocks
```

## Deploy to 4EVERLAND — Hosting (Task 3)

4EVERLAND's **Hosting** product builds from a Git branch and pins the
output directory on IPFS. To publish this folder:

1. 4EVERLAND Dashboard → Hosting → **New Project**.
2. Import the GitHub repo, pick branch `lab18`.
3. Build settings:

   | Field | Value |
   |-------|-------|
   | Framework | None / Static HTML |
   | Install command | *(empty — no build step)* |
   | Build command   | *(empty — no build step)* |
   | Output directory | `ipfs-site` |

4. Click **Deploy**. 4EVERLAND will return:
   - a platform URL like `https://<slug>.4everland.app`
   - an IPFS CID pinned on their infrastructure
   - that same CID reachable on `https://ipfs.4everland.link/ipfs/<CID>`
     and other public gateways.

In this submission, the local Kubo CID
(`bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq`) **did**
match the 4EVERLAND build CID byte-for-byte for both rev-1 and rev-2 —
no `_headers` / `_redirects` injection, no trailing-newline drift.
That cross-implementation reproducibility is the headline result of
the lab, see `../../4EVERLAND.md` §1 and §6 for the side-by-side.

## Pin to 4EVERLAND — Bucket (Task 4)

1. Dashboard → Bucket → **Create Bucket**.
2. Drag-and-drop `index.html` (or an asset bundle).
3. Each uploaded file gets its own CID; folder uploads produce a
   directory CID identical to `ipfs add -r --cid-version=1`.
4. Verify resolution across gateways:

   ```bash
   for gw in \
       https://ipfs.4everland.link \
       https://ipfs.io \
       https://dweb.link \
       https://cloudflare-ipfs.com ; do
     curl -s -o /dev/null -w "%{http_code}  %{time_total}s  $gw\n" \
          "$gw/ipfs/<CID>"
   done
   ```

   Document the output in
   [`evidence/20-public-gateways-after-pin.txt`](./evidence/) (created
   by the user after the real 4EVERLAND pin is in place).

## Why a static HTML file?

The landing page is a single self-contained file — no build tool, no
external JS, no API calls. That keeps the IPFS DAG tiny
(2 blocks, 31 KiB — see [`evidence/10-ipfs-stats.txt`](./evidence/10-ipfs-stats.txt))
and means content addressing works without any "same commit, different
build" drift. It's the decentralised-hosting analogue of the
"single-file Worker" in Lab 17.
