# Lab 18 - Decentralized Hosting with 4EVERLAND and IPFS

This document describes the Lab 18 solution: local IPFS fundamentals,
4EVERLAND deployment, IPFS pinning, mutable updates, and the comparison between
traditional hosting and decentralized hosting.

## Summary

| Item | Value |
| --- | --- |
| Static site | `labs/lab18/index.html` |
| Local IPFS stack | `labs/lab18/docker-compose.yml` |
| Bucket sample folder | `labs/lab18/ipfs-sample` |
| 4EVERLAND project name | `devops-core-course-lab18` |
| Hosting root directory | `labs/lab18` |
| Build command | empty |
| Output directory | empty or `.` |
| Deployment network | IPFS |

Final deployment fields to fill after deploying from the 4EVERLAND dashboard:

| Field | Value |
| --- | --- |
| 4EVERLAND URL | `https://<project>.4everland.app` |
| IPFS CID, first deploy | `<CID-1>` |
| IPFS CID, redeploy | `<CID-2>` |
| 4EVERLAND gateway | `https://ipfs.4everland.io/ipfs/<CID>` |
| IPFS.io gateway | `https://ipfs.io/ipfs/<CID>` |
| DWeb gateway | `https://dweb.link/ipfs/<CID>` |

## Task 1 - IPFS Fundamentals

IPFS uses content addressing. A CID identifies content by data-derived hash and
metadata, not by the server location. If content changes, the CID changes. If
the same content is added with the same settings, it gets the same CID.

Key concepts:

| Concept | Meaning |
| --- | --- |
| Content addressing | Request content by what it is, not where it is hosted |
| CID | Content Identifier for an IPFS object |
| Pinning | Mark content to keep it and prevent garbage collection |
| Gateway | HTTP bridge for accessing IPFS content from a browser |
| IPNS | Mutable name that can point to changing IPFS CIDs |

Run a local IPFS node with Docker Compose:

```powershell
cd labs/lab18
docker compose up -d
docker exec lab18-ipfs ipfs version
```

Open the Kubo Web UI:

```text
http://localhost:5001/webui
```

Add the sample file to local IPFS:

```powershell
docker cp ipfs-sample/hello.txt lab18-ipfs:/export/hello.txt
docker exec lab18-ipfs ipfs add /export/hello.txt
```

Expected output format:

```text
added <HELLO_FILE_CID> hello.txt
```

Read it through the local gateway:

```powershell
curl.exe http://localhost:8080/ipfs/<HELLO_FILE_CID>
```

Add the full static site directory:

```powershell
docker cp index.html lab18-ipfs:/export/index.html
docker exec lab18-ipfs ipfs add -r /export
```

The last CID in the recursive output is the directory CID.

Stop the local node:

```powershell
docker compose down
```

## Task 2 - 4EVERLAND Setup

Create an account:

1. Open `https://www.4everland.org/`.
2. Sign in with GitHub or wallet.
3. Open the dashboard.
4. Review Hosting, Bucket, Gateway, and Domains.

4EVERLAND services used in this lab:

| Service | Purpose |
| --- | --- |
| DWeb Hosting | Deploy the static site to IPFS |
| Bucket | Upload and pin files/folders |
| Gateway | Serve IPFS content through HTTPS |
| Domains | Keep a stable project URL while the underlying CID changes |

## Task 3 - Deploy Static Content

The static site is already available at:

```text
labs/lab18/index.html
```

Deploy through 4EVERLAND:

1. Open 4EVERLAND Dashboard.
2. Go to Hosting.
3. Click New Project.
4. Import the GitHub repository.
5. Select the branch with Lab 18 changes.
6. Set deployment platform to IPFS.
7. Configure build settings:

| Setting | Value |
| --- | --- |
| Framework preset | Other / Static |
| Root directory | `labs/lab18` |
| Build command | empty |
| Output directory | empty or `.` |

After deployment, record:

```text
Project URL: https://<project>.4everland.app
CID: <CID-1>
Gateway URL: https://ipfs.4everland.io/ipfs/<CID-1>
```

Verify:

```powershell
curl.exe -I https://<project>.4everland.app
curl.exe -I https://ipfs.4everland.io/ipfs/<CID-1>
```

Permanence test:

1. Make a small visible change in `labs/lab18/index.html`.
2. Commit and push.
3. Redeploy in 4EVERLAND.
4. Record the new CID.

Expected result:

```text
Project URL stays the same.
CID changes from <CID-1> to <CID-2>.
Old CID remains immutable and still points to old content.
```

## Task 4 - IPFS Pinning with Bucket

Sample files for Bucket upload:

```text
labs/lab18/ipfs-sample/hello.txt
labs/lab18/ipfs-sample/course.json
```

Upload files:

1. Open Dashboard.
2. Go to Bucket.
3. Create a bucket, for example `devops-core-lab18`.
4. Upload `hello.txt`.
5. Upload `course.json`.
6. Record each file CID.

Upload a folder:

1. Upload the whole `labs/lab18/ipfs-sample` folder.
2. Record the directory CID.
3. Access files through `gateway/ipfs/<DIR_CID>/hello.txt`.

Gateway verification:

```text
https://ipfs.4everland.io/ipfs/<CID>
https://ipfs.io/ipfs/<CID>
https://dweb.link/ipfs/<CID>
```

Note: if a public gateway blocks HTML content for abuse-prevention reasons,
use the assigned 4EVERLAND project domain for the website and use gateways for
static assets or non-HTML Bucket objects. The deployed Hosting project still
records the IPFS hash/CID for the build.

Results table:

| Object | CID | 4EVERLAND gateway | IPFS.io | DWeb |
| --- | --- | --- | --- | --- |
| `hello.txt` | `<HELLO_CID>` | Works / pending | Works / pending | Works / pending |
| `course.json` | `<JSON_CID>` | Works / pending | Works / pending | Works / pending |
| `ipfs-sample/` | `<DIR_CID>` | Works / pending | Works / pending | Works / pending |

Pinning explanation:

Uploading through Bucket stores the object and pins it so it remains available.
An unpinned object may disappear when the node that originally had it runs
garbage collection or goes offline.

## Task 5 - IPNS and Updates

IPFS CIDs are immutable. Every content change creates a new CID. This is good
for integrity and reproducibility, but not enough for normal websites that need
stable URLs.

IPNS and 4EVERLAND project domains solve this by using a stable pointer:

| Mechanism | Behavior |
| --- | --- |
| IPFS CID | Immutable content address |
| IPNS | Mutable name pointing to a current CID |
| 4EVERLAND project URL | Stable HTTPS URL for users |
| Custom domain | Stable domain mapped to the latest deployment |

Update flow:

1. Change `index.html`.
2. Redeploy.
3. The 4EVERLAND project URL stays the same.
4. The deployment CID changes.
5. Old CID remains accessible as an immutable snapshot.

## Task 6 - Documentation and Analysis

Screenshots to capture:

| File | Evidence |
| --- | --- |
| `screenshots/lab18/01-local-ipfs-webui.png` | Local IPFS Web UI |
| `screenshots/lab18/02-local-gateway.png` | Local gateway serves CID |
| `screenshots/lab18/03-4everland-dashboard.png` | 4EVERLAND project dashboard |
| `screenshots/lab18/04-deployed-site.png` | Deployed site |
| `screenshots/lab18/05-ipfs-gateway.png` | Site through IPFS gateway |
| `screenshots/lab18/06-bucket-storage.png` | Bucket with uploaded files |
| `screenshots/lab18/07-multiple-gateways.png` | Same CID through multiple gateways |
| `screenshots/lab18/08-redeploy-new-cid.png` | Updated deploy with new CID |

## Traditional Hosting vs IPFS/4EVERLAND

| Aspect | Traditional Hosting | IPFS/4EVERLAND |
| --- | --- | --- |
| Content addressing | Usually URL/location based | CID/content based |
| Single point of failure | Depends on one provider or region unless replicated | Content can be fetched from multiple peers/gateways |
| Censorship resistance | Provider or domain can remove content | Stronger when content is pinned across providers |
| Update mechanism | Replace files behind the same URL | New CID plus mutable pointer/domain |
| Cost model | Pay for servers, CDN, storage, operations | Pay for storage, bandwidth, pinning, hosting tier |
| Speed/latency | Excellent with mature CDN setup | Good with accelerated gateways, variable with public gateways |
| Integrity | Requires trust in origin and TLS | CID verifies content identity |
| Best use cases | Dynamic apps, APIs, auth-heavy systems | Static sites, public assets, NFTs, archival content |

## When Decentralized Hosting Makes Sense

Use IPFS/4EVERLAND when:

- the content is static or mostly static;
- content integrity and verifiability matter;
- public assets should survive origin outages;
- immutable versions are useful;
- the project benefits from Web3-native infrastructure.

## When Traditional Hosting Is Better

Use traditional hosting when:

- server-side rendering or dynamic APIs are required;
- strong access control and private data are central;
- low-latency writes or database-backed workflows are needed;
- operational teams already depend on cloud-native services;
- compliance requires specific data residency guarantees.

## Recommendation

For the provided Lab 18 landing page, 4EVERLAND and IPFS are a strong fit. The
site is static, public, and benefits from immutable CIDs and gateway access. For
the FastAPI DevOps Info Service from earlier labs, Fly.io or Kubernetes remains
the better fit because the app has runtime state, health checks, metrics, and a
dynamic HTTP API.

## Local Verification Status

The repository now contains all files needed for Lab 18. Final external proof
requires access to Docker and a 4EVERLAND account.

Current workspace limitation:

```text
Docker daemon access was not available from this execution environment.
4EVERLAND deployment requires account login in the browser dashboard.
```

Run these commands locally to complete real verification:

```powershell
cd labs/lab18
docker compose up -d
docker cp ipfs-sample/hello.txt lab18-ipfs:/export/hello.txt
docker exec lab18-ipfs ipfs add /export/hello.txt
```

Then deploy `labs/lab18` through 4EVERLAND Hosting and fill the CID/URL fields
at the top of this document.

## Final Checklist

- [x] IPFS concepts documented
- [x] Local IPFS Docker Compose created
- [x] Sample files prepared for local IPFS and Bucket upload
- [x] Static site deployment settings documented
- [x] Bucket pinning workflow documented
- [x] Multiple gateway checks documented
- [x] IPNS and update behavior explained
- [x] Centralized vs decentralized comparison completed
- [x] Screenshot checklist created
- [ ] Local Docker IPFS run captured
- [ ] 4EVERLAND project deployed
- [ ] CIDs and URLs filled in
- [ ] Screenshots captured

## References

- IPFS CIDs and content addressing: https://docs.ipfs.tech/concepts/content-addressing/
- 4EVERLAND Hosting deployment: https://docs.4everland.org/hositng/guides/site-deployment
- 4EVERLAND Bucket storage: https://docs.4everland.org/storage/bucket
- 4EVERLAND IPFS gateway: https://docs.4everland.org/gateways
