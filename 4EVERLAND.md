# Lab 18 - 4EVERLAND & IPFS

## Summary

For Lab 18, I prepared and verified a decentralized hosting workflow around IPFS, a local Kubo node, a deployable static site, a recursive "bucket" directory, and bonus automation scripts.

What was completed autonomously in this workspace:

- studied and documented IPFS fundamentals
- started a local IPFS Kubo node in Docker
- added content locally and recorded the resulting CIDs
- verified local gateway access and local pinning
- demonstrated immutable updates by changing the site and observing a new CID
- prepared bonus automation scripts for repeatable publish and gateway checks

What could not be completed without account secrets:

- authenticated 4EVERLAND Hosting or Bucket deployment
- real 4EVERLAND project URL
- real 4EVERLAND-hosted CID and IPNS/domain binding

The blocker is external authentication. The 4EVERLAND CLI is installed and works, but `login` requires a personal token and the browser login flow stops on GitHub sign-in.

## Task 1 - IPFS Fundamentals

### Concepts

- **Content addressing** identifies content by its bytes rather than by server location.
- **CID** changes when content changes, so integrity is built into the address itself.
- **Pinning** keeps content from being removed by garbage collection.
- **Gateway** exposes IPFS content over HTTP.

Supporting notes:

- [labs/lab18/ipfs-content/ipfs-concepts.md](</Users/pavorkmert/studying/DevOps/DevOps-Core-Course — копия/labs/lab18/ipfs-content/ipfs-concepts.md>)

### Local Kubo node

Command used:

```bash
docker run -d --name ipfs-lab18 \
  -p 4001:4001 \
  -p 8080:8080 \
  -p 5001:5001 \
  ipfs/kubo:latest
```

Local endpoints:

- Web UI: `http://localhost:5001/webui`
- Gateway: `http://localhost:8080`

Screenshot:

![IPFS Web UI](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course — копия/labs/lab18/screenshots/ipfs-webui.png)

### Local content added

Test file:

- [labs/lab18/ipfs-content/hello.txt](</Users/pavorkmert/studying/DevOps/DevOps-Core-Course — копия/labs/lab18/ipfs-content/hello.txt>)
- CID: `Qmf8gp1E9J6agtxfUMQ9qMjFg2zSmeberT7PizKc4xMvPr`
- Local gateway URL: `http://localhost:8080/ipfs/Qmf8gp1E9J6agtxfUMQ9qMjFg2zSmeberT7PizKc4xMvPr`

## Task 2 - 4EVERLAND Setup

### Platform understanding

Reviewed the official 4EVERLAND service model:

- Hosting for static deployments on decentralized storage
- Bucket for stored files and directory pinning
- Gateway and IPNS-oriented access patterns

CLI validation completed locally:

```bash
npx -y @4everland/hosting-cli -v
# 1.0.11

npx -y @4everland/hosting-cli -h
# commands: login, deploy, cid, ipns, domain, getipns, update
```

### Auth blocker

The dashboard is reachable, but not authenticated in this environment:

![4EVERLAND login](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course — копия/labs/lab18/screenshots/4everland-login.png)

Observed behavior:

- `https://dashboard.4everland.org/login` opens correctly
- GitHub OAuth redirects to GitHub sign-in
- `npx -y @4everland/hosting-cli login` prompts: `Please enter your Token:`

Because no 4EVERLAND token or logged-in GitHub session exists in this environment, the actual remote deployment step cannot be finished honestly from here.

## Task 3 - Static Content Deployment

### Static site used

Base file:

- [labs/lab18/index.html](</Users/pavorkmert/studying/DevOps/DevOps-Core-Course — копия/labs/lab18/index.html>)

I kept the provided landing page and added a tiny verification marker to produce a second immutable version:

- `Lab 18 verification build: v2 content-addressing update.`

### Site CIDs

- Site v1 CID: `QmSAT1vb9LsfKiSGoptLgiTsjrzjnVfSb3GWpSbsiQNqNe`
- Site v2 CID: `QmXQBaHTr678RpxSQL9RxVxmtar8FCdSzrJ9uhzLkeyghV`

This proves the key IPFS rule:

- same content -> same CID
- changed content -> new CID

### Local deployment verification

Local gateway URL for current site:

- `http://localhost:8080/ipfs/QmXQBaHTr678RpxSQL9RxVxmtar8FCdSzrJ9uhzLkeyghV/`

Screenshot:

![Site on local IPFS gateway](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course — копия/labs/lab18/screenshots/site-v2-local-gateway.png)

## Task 4 - IPFS Pinning

### Bucket-style directory prepared

Directory:

- [labs/lab18/bucket/README.md](</Users/pavorkmert/studying/DevOps/DevOps-Core-Course — копия/labs/lab18/bucket/README.md>)
- [labs/lab18/bucket/gateway-notes.md](</Users/pavorkmert/studying/DevOps/DevOps-Core-Course — копия/labs/lab18/bucket/gateway-notes.md>)
- [labs/lab18/bucket/data/course-roadmap.json](</Users/pavorkmert/studying/DevOps/DevOps-Core-Course — копия/labs/lab18/bucket/data/course-roadmap.json>)

Directory CID:

- `Qmak7oJ7g3crKqupmds1gHJraN4bYJjtQ4Xc1DrKUNDpbk`

Local path-based gateway access:

- `http://localhost:8080/ipfs/Qmak7oJ7g3crKqupmds1gHJraN4bYJjtQ4Xc1DrKUNDpbk/`
- `http://localhost:8080/ipfs/Qmak7oJ7g3crKqupmds1gHJraN4bYJjtQ4Xc1DrKUNDpbk/data/course-roadmap.json`

Screenshot:

![Bucket directory over local gateway](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course — копия/labs/lab18/screenshots/bucket-directory-local-gateway.png)

### Pin verification

The local node reports the uploaded content as recursively pinned:

- `Qmf8gp1E9J6agtxfUMQ9qMjFg2zSmeberT7PizKc4xMvPr`
- `Qmak7oJ7g3crKqupmds1gHJraN4bYJjtQ4Xc1DrKUNDpbk`
- `QmSAT1vb9LsfKiSGoptLgiTsjrzjnVfSb3GWpSbsiQNqNe`

### Multi-gateway observation

I tested the site CID against:

- local Kubo gateway
- `ipfs.io`
- `dweb.link`
- `cloudflare-ipfs.com`

Result:

- local gateway served the content immediately
- public gateways did not fetch the content successfully during the test window

Interpretation:

- the content exists and is pinned on the local node
- but it is not pinned by a public persistence provider such as 4EVERLAND Bucket
- this is exactly why managed pinning matters for reliable public retrieval

## Task 5 - IPNS and Updates

### IPFS vs IPNS

- **IPFS CID** is immutable and changes when bytes change
- **IPNS** is a stable mutable name that can point to a new CID

### Practical observation from this lab

When I changed the landing page footer, the CID changed from:

- `QmSAT1vb9LsfKiSGoptLgiTsjrzjnVfSb3GWpSbsiQNqNe`

to:

- `QmXQBaHTr678RpxSQL9RxVxmtar8FCdSzrJ9uhzLkeyghV`

This demonstrates immutable content addressing directly.

### 4EVERLAND update model

4EVERLAND Hosting is useful here because it keeps a stable project URL while updating the underlying published content, which is the practical user-facing equivalent of an IPNS-backed or managed update flow.

## Task 6 - Analysis

### Centralized vs Decentralized Hosting

| Aspect | Traditional Hosting | IPFS / 4EVERLAND |
|---|---|---|
| Content addressing | Location-based (`domain -> server`) | Content-based (`CID -> bytes`) |
| Single point of failure | Higher | Lower when pinned and replicated |
| Censorship resistance | Lower | Higher |
| Update mechanism | Replace files in place | New CID for changed content, stable front door via IPNS/project URL |
| Cost model | Server/runtime centric | Storage, bandwidth, pinning, and gateway centric |
| Speed / latency | Predictable with CDN | Depends on gateway, cache, and provider availability |
| Best use cases | Dynamic apps, APIs, databases | Static sites, public assets, archives, verifiable artifacts |

### When decentralized hosting makes sense

- public static sites
- educational materials
- artifacts that benefit from integrity verification
- content that should remain available from multiple providers

### When traditional hosting is better

- dynamic applications with server-side logic
- systems with databases and user sessions
- workloads needing strict latency control or private backend networks

### Recommendation

Best hybrid pattern:

- keep static frontend or public artifacts on IPFS / 4EVERLAND
- keep dynamic APIs and databases on traditional infrastructure

## Bonus Task

Lab 18 does not define a separate explicit bonus section in `labs/lab18.md`, so I implemented a practical bonus automation package instead.

Bonus files:

- [labs/lab18/bonus/README.md](</Users/pavorkmert/studying/DevOps/DevOps-Core-Course — копия/labs/lab18/bonus/README.md>)
- [labs/lab18/bonus/publish-local-demo.sh](</Users/pavorkmert/studying/DevOps/DevOps-Core-Course — копия/labs/lab18/bonus/publish-local-demo.sh>)
- [labs/lab18/bonus/verify-lab18.sh](</Users/pavorkmert/studying/DevOps/DevOps-Core-Course — копия/labs/lab18/bonus/verify-lab18.sh>)

What they do:

- `publish-local-demo.sh` starts a local Kubo node, uploads the lab assets, and prints resulting CIDs
- `verify-lab18.sh <cid>` checks the same CID through local and public gateways

## Completion Status

Checklist status for this workspace:

- [x] IPFS concepts understood and documented
- [x] Local IPFS node running
- [x] Content added to local IPFS
- [ ] 4EVERLAND account authenticated
- [ ] Static site deployed via authenticated 4EVERLAND account
- [ ] Files uploaded to authenticated 4EVERLAND Bucket
- [x] Local and public gateway behavior tested
- [x] IPNS / update behavior explained
- [x] `4EVERLAND.md` documentation completed
- [x] Comparison analysis completed

## Only Remaining External Step

To finish the real remote 4EVERLAND publish, this environment needs one of:

1. a 4EVERLAND Hosting token for `npx -y @4everland/hosting-cli login`
2. a logged-in browser session that can complete GitHub OAuth

After that, the prepared site directory is ready for upload without any commit.
