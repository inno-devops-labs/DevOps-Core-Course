# Lab 18 - Decentralized Hosting with 4EVERLAND and IPFS

Run date: April 15, 2026

Resource-saving note:
I did not authenticate to 4EVERLAND or run a live Kubo container in this session. Instead, I prepared reusable local IPFS assets in `labs/lab18`, kept the provided static site ready for direct hosting deployment, and documented the exact workflows needed for a real account-backed run.

## Files Added

- `labs/lab18/docker-compose.yml`
- `labs/lab18/ipfs-demo/hello-ipfs.txt`
- `labs/lab18/ipfs-demo/course-metadata.json`
- `labs/lab18/ipfs-demo/assets/course-badge.svg`
- `labs/lab18/ipfs-demo/notes/roadmap.txt`
- `4EVERLAND.md`

Existing deployable site used for this lab:

- `labs/lab18/index.html`

## Local Validation

Validation commands:

```text
py -3 -c "import json, pathlib; json.loads(pathlib.Path('labs/lab18/ipfs-demo/course-metadata.json').read_text(encoding='utf-8')); print('ipfs-demo-json-ok')"
docker compose -f labs/lab18/docker-compose.yml config
```

What was validated locally:

- the sample Bucket/IPFS metadata file is valid JSON
- `docker compose -f labs/lab18/docker-compose.yml config` rendered successfully
- the repository now contains both a static site (`labs/lab18/index.html`) and a multi-file demo directory (`labs/lab18/ipfs-demo`) for CID and pinning exercises

## IPFS Fundamentals

### Content addressing vs location addressing

- traditional hosting usually retrieves content from a location such as `https://example.com/page.html`
- IPFS identifies content by CID, so the address is derived from the content rather than the server location
- IPFS docs state that the same content added with the same settings produces the same CID, while any content change produces a different CID

### CIDs

- a CID is the identifier you receive after adding content to IPFS
- a CID points to the content itself, not to a particular machine or URL
- for small demos you will often see a CIDv0 starting with `Qm...`, while modern browser-safe forms often use CIDv1 and start with `bafy...`

### Pinning and garbage collection

- IPFS nodes cache and exchange data, but disk space is finite
- unneeded cached content can be removed by garbage collection
- pinning protects content from garbage collection and is the core reason pinning services exist

### Gateways

- gateways bridge normal HTTP browsers and the peer-to-peer IPFS network
- 4EVERLAND documents both path-style and subdomain-style gateway URLs for IPFS content
- public gateways are useful for verification, but project hosting URLs are usually the cleanest way to serve a site to end users

## Local IPFS Node

Prepared local helper: `labs/lab18/docker-compose.yml`

It runs `ipfs/kubo` with:

- API on `http://localhost:5001`
- gateway on `http://localhost:8080`
- swarm port `4001`
- the repo folder `labs/lab18/ipfs-demo` mounted read-only at `/pins`

Prepared local workflow:

```powershell
cd .\labs\lab18
docker compose up -d
docker exec lab18-ipfs ipfs add /pins/hello-ipfs.txt
docker exec lab18-ipfs ipfs add -Qr /pins
```

What the commands do:

- the first `ipfs add` returns a CID for a single file
- the recursive `-Qr` add returns the root CID for the whole directory tree
- that root CID can then be used to retrieve nested files through a gateway

Prepared local verification:

```powershell
curl http://localhost:8080/ipfs/<CID>
curl http://localhost:8080/ipfs/<DIR_CID>/hello-ipfs.txt
curl http://localhost:8080/ipfs/<DIR_CID>/notes/roadmap.txt
```

Prepared local Web UI:

- `http://localhost:5001/webui`

## 4EVERLAND Setup and Services

The 4EVERLAND docs currently expose these relevant product areas:

- Hosting
- Bucket
- IPFS Gateway
- IPNS Manager

Prepared account workflow:

1. Sign in to the 4EVERLAND dashboard.
2. Review Hosting for site deployment.
3. Review Bucket for IPFS uploads and pinning.
4. Review Gateway and IPNS Manager for public access and stable names.

I did not include numeric free-tier claims here because plan limits can change. Review the current Billing/Pricing page in the 4EVERLAND docs before relying on any quota.

## Deploy Static Content

Prepared static site:

- `labs/lab18/index.html`

Prepared hosting steps:

1. Open 4EVERLAND Dashboard -> Hosting.
2. Create a new project from the GitHub repository.
3. Choose the branch `lab18`.
4. Use no framework preset for the static site.
5. Leave the build command empty.
6. Set the output directory to `labs/lab18`.
7. Deploy.

Expected post-deploy checks:

- open the stable 4EVERLAND project URL
- confirm the landing page loads
- record the generated CID shown by the platform for that deploy

Prepared update test:

1. Change any content in `labs/lab18/index.html`.
2. Redeploy the same project.
3. Confirm the project URL stays the same but the underlying CID changes.

## Bucket Uploads and Pinning

Prepared upload directory:

- `labs/lab18/ipfs-demo`

Why this directory is useful:

- it contains multiple files
- it includes a nested `notes/` directory
- it is suitable for both local Kubo adds and 4EVERLAND Bucket uploads

Prepared Bucket workflow:

1. Open Dashboard -> Bucket.
2. Create an IPFS bucket.
3. Upload the whole `labs/lab18/ipfs-demo` directory.
4. Record the directory CID and one or two file-level CIDs.

Prepared gateway checks:

- 4EVERLAND path style: `https://4everland.io/ipfs/<DIR_CID>/hello-ipfs.txt`
- 4EVERLAND subdomain style: `https://<DIR_CID>.ipfs.4everland.io/hello-ipfs.txt`
- IPFS.io: `https://ipfs.io/ipfs/<DIR_CID>/hello-ipfs.txt`
- DWeb.link: `https://dweb.link/ipfs/<DIR_CID>/hello-ipfs.txt`

Important 4EVERLAND gateway note:

- as of April 15, 2026, the 4EVERLAND IPFS Gateway docs say the public gateway does not support HTML content
- use the Hosting project URL for the website itself, and use gateway checks primarily for raw files or to confirm CID accessibility

## IPNS and Updates

Core model:

- IPFS CID = immutable content pointer
- IPNS name = mutable pointer that can be updated to the latest CID

The IPFS docs describe IPNS as a mutable pointer layer over immutable CIDs. The 4EVERLAND IPNS Manager docs describe creating custom name records that resolve to current IPFS content.

Prepared local IPNS workflow with Kubo:

```powershell
docker exec lab18-ipfs ipfs add -Qr /pins
docker exec lab18-ipfs ipfs name publish /ipfs/<DIR_CID>
docker exec lab18-ipfs ipfs name resolve self
```

Prepared 4EVERLAND workflow:

1. Open Dashboard -> Gateway -> IPNS Manager.
2. Create an IPNS record for the latest site CID or Bucket CID.
3. Update the project or directory later.
4. Repoint the IPNS name to the new CID while keeping the same published name.

## Deployment Summary

Prepared artifacts:

- static site directory: `labs/lab18`
- local IPFS demo directory: `labs/lab18/ipfs-demo`
- local Kubo helper: `labs/lab18/docker-compose.yml`

Expected live outputs from a real run:

- one stable 4EVERLAND Hosting URL
- one or more immutable CIDs for site and Bucket uploads
- optional IPNS name for the mutable entrypoint

Because no authenticated 4EVERLAND session was used, I did not record a real project URL, Bucket URL, CID list, or dashboard screenshots.

## Screenshots To Capture In A Live Run

When running this lab against a real account, capture:

- Hosting project dashboard
- deployed landing page
- Bucket directory view with CIDs
- the same CID opened through at least two gateways
- IPNS Manager entry after publishing

## Centralized vs Decentralized Hosting

| Aspect | Traditional Hosting | IPFS/4EVERLAND |
|--------|---------------------|----------------|
| Content addressing | URL points to a server location | CID points to content |
| Single point of failure | Higher risk if provider or origin fails | Lower if content is pinned and replicated |
| Censorship resistance | Usually weaker | Usually stronger |
| Update mechanism | Replace content in place | Publish new CID, optionally keep stable access through IPNS or project URL |
| Cost model | Usually server or platform billing | Mix of hosting, storage, bandwidth, and pinning economics |
| Speed and latency | Predictable with CDN and origin tuning | Can be strong through gateways and edge nodes, but depends on pinning and gateway path |
| Best use cases | Dynamic apps, databases, frequent server-side logic | Static sites, public assets, archives, verifiable content distribution |

## Use Case Analysis

Decentralized hosting makes the most sense when:

- you want verifiable content integrity
- you want resilient public distribution across multiple gateways
- your workload is mostly static content or documents

Traditional hosting is better when:

- you need server-side compute, databases, or low-friction mutable state
- you need strong transactional guarantees
- you want the simplest operational model for a standard web app

My recommendation:

- use 4EVERLAND and IPFS for static sites, public artifacts, and immutable releases
- keep conventional hosting or a platform like Fly.io for stateful or compute-heavy applications
- if you want the strongest result for this course lab, combine both models: host the static landing page on 4EVERLAND and keep the Python API on a conventional platform
