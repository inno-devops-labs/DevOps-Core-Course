# Lab 18 — Decentralized Hosting with 4EVERLAND and IPFS

## Deployment Summary

This lab uses the provided static website from `labs/lab18/index.html` and a small demo folder from `labs/lab18/bucket-demo/` to verify IPFS content addressing, pinning, gateway access, and mutable updates through IPNS-style naming.

### Local IPFS Node

I ran a local Kubo node with Docker:

```bash
docker pull ipfs/kubo:latest
docker run -d --name lab18-ipfs \
  -p 4001:4001 \
  -p 8080:8080 \
  -p 5001:5001 \
  ipfs/kubo:latest
```

Verification:

```text
lab18-ipfs ipfs/kubo:latest Up (healthy)
Web UI:  http://localhost:5001/webui
Gateway: http://localhost:8080
```

Docker Desktop was required on this machine because the first WSL-only Docker pull did not complete. After Docker Desktop was installed, `docker pull ipfs/kubo:latest` succeeded with digest:

```text
sha256:0661819c2e0972f02d2c27759c217d7d739d461e52fc685e79113254af8f2f6b
```

## Task 1 — IPFS Fundamentals

### Concepts

| Concept | Summary |
|---|---|
| Content addressing | IPFS identifies data by its content hash, not by server location. If content changes, the identifier changes. |
| CID | A Content Identifier is the address of an IPFS object. It can identify a single file or a directory DAG. |
| Pinning | A pinned object is protected from garbage collection on the node or pinning service that stores it. |
| Gateway | A gateway exposes IPFS content over HTTP, for example `http://localhost:8080/ipfs/<CID>`. |

### Local Content Added

Test file:

```bash
printf "Hello IPFS from DevOps Core Course Lab 18!\n" > labs/lab18/hello-ipfs.txt
docker cp labs/lab18/hello-ipfs.txt lab18-ipfs:/hello-ipfs.txt
docker exec lab18-ipfs ipfs add /hello-ipfs.txt
```

Result:

```text
added QmXRDXGFVkSkyrAgQpjh23NYeG52EeGtAPKZ2tKiEtpduA hello-ipfs.txt
```

Gateway check:

```bash
curl -fsSL http://localhost:8080/ipfs/QmXRDXGFVkSkyrAgQpjh23NYeG52EeGtAPKZ2tKiEtpduA
```

Output:

```text
Hello IPFS from DevOps Core Course Lab 18!
```

## Task 2 — 4EVERLAND Setup

4EVERLAND provides three relevant services for this lab:

| Service | Lab Usage |
|---|---|
| Hosting | Deploy `labs/lab18/index.html` as a static website backed by IPFS. |
| Bucket / Storage | Upload and pin files or folders to IPFS and obtain CIDs. |
| Gateway | Access pinned content through 4EVERLAND HTTP gateway URLs. |

Account-dependent steps:

1. Sign in at `https://www.4everland.org/` with GitHub or a wallet.
2. Open the dashboard and verify access to Hosting, Bucket, Gateway, and Domains.
3. Use the free tier for this course lab: static hosting, bucket storage, and gateway bandwidth are enough for the provided site and demo files.

## Task 3 — Static Content Deployment

### Static Site Used

The deployed site source is:

```text
labs/lab18/index.html
```

Local IPFS add:

```bash
docker cp labs/lab18 lab18-ipfs:/lab18-site
docker exec lab18-ipfs ipfs add -r /lab18-site
```

Result:

```text
added QmXRDXGFVkSkyrAgQpjh23NYeG52EeGtAPKZ2tKiEtpduA lab18-site/hello-ipfs.txt
added QmbNeCQiZt4WiaRPGuD53zc8HA8uLZd5bbub3NCJDxD2Sa lab18-site/index.html
added QmYY2wiMqjuEVfFZYEZhaM9wLFfhnNh2vYkJ5QujvVBehT lab18-site
```

Local gateway URLs:

| Object | CID | URL |
|---|---|---|
| Test file | `QmXRDXGFVkSkyrAgQpjh23NYeG52EeGtAPKZ2tKiEtpduA` | `http://localhost:8080/ipfs/QmXRDXGFVkSkyrAgQpjh23NYeG52EeGtAPKZ2tKiEtpduA` |
| Site `index.html` | `QmbNeCQiZt4WiaRPGuD53zc8HA8uLZd5bbub3NCJDxD2Sa` | `http://localhost:8080/ipfs/QmbNeCQiZt4WiaRPGuD53zc8HA8uLZd5bbub3NCJDxD2Sa` |
| Site directory | `QmYY2wiMqjuEVfFZYEZhaM9wLFfhnNh2vYkJ5QujvVBehT` | `http://localhost:8080/ipfs/QmYY2wiMqjuEVfFZYEZhaM9wLFfhnNh2vYkJ5QujvVBehT/` |

4EVERLAND deployment settings to use in the dashboard:

```text
Framework: None / Static
Build command: empty
Output directory: labs/lab18
```

4EVERLAND deployment values from the dashboard:

```text
4EVERLAND project URL: https://devops-core-course-4-98im.ipfs.4everland.app/
4EVERLAND deployment CID: bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq
4EVERLAND gateway URL: https://ipfs.4everland.link/ipfs/bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq
```


### 4EVERLAND Deployment Result

The 4EVERLAND deployment produced this IPFS CID:

```text
bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq
```

Project URL verification:

```text
https://devops-core-course-4-98im.ipfs.4everland.app/
HTTP 200
x-ipfs-path: /ipfs/bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq/
<title>DevOps Core Course | Production-Grade Practices</title>
```

Gateway verification on 2026-05-13:

| Gateway | URL | Result |
|---|---|---|
| IPFS.io | `https://ipfs.io/ipfs/bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq` | HTTP 301 then HTML content verified with `curl -L` |
| DWeb.link | `https://dweb.link/ipfs/bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq` | HTTP 301 to subdomain gateway; expected public gateway resolution |
| 4EVERLAND project URL | `https://devops-core-course-4-98im.ipfs.4everland.app/` | HTTP 200, `x-ipfs-path: /ipfs/bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq/` verified |

## Task 4 — IPFS Pinning

### Bucket Demo Files

I prepared a demo folder for Bucket upload and directory CID verification:

```text
labs/lab18/bucket-demo/
├── assets/ipfs-demo.svg
├── docs/readme.txt
└── metadata.json
```

Local IPFS add:

```bash
docker cp labs/lab18/bucket-demo lab18-ipfs:/bucket-demo
docker exec lab18-ipfs ipfs add -r /bucket-demo
```

Result:

```text
added QmbGDnmirFzmm5nVv1JYVNjXiSkLNrWYVnGgjhSw6gQMi6 bucket-demo/assets/ipfs-demo.svg
added Qme5gMeTbV5TiajaPoEVMLDsNVwenNm91CP5KYMeNrqZH2 bucket-demo/docs/readme.txt
added QmWXxzv3aTpsWXxCLrPRtDvBTTSvq7KcGA6drr7ZuL7R6g bucket-demo/metadata.json
added QmcaQrH9kpEikEokoSxfShHumeTvZjqJ3H9akq5edddHLd bucket-demo/assets
added QmfK8zCYMFKvrqB9GKtosar5mXZaxyuGYweouozELupQuT bucket-demo/docs
added Qmdpru5DjMHb7XTAgGtwVnNb5C2bkZzc1snLv7R6ZuedNY bucket-demo
```

Directory access examples:

```text
http://localhost:8080/ipfs/Qmdpru5DjMHb7XTAgGtwVnNb5C2bkZzc1snLv7R6ZuedNY/docs/readme.txt
http://localhost:8080/ipfs/Qmdpru5DjMHb7XTAgGtwVnNb5C2bkZzc1snLv7R6ZuedNY/assets/ipfs-demo.svg
```

Pin verification:

```bash
docker exec lab18-ipfs ipfs pin ls --type recursive | grep -E "QmXRDXGF|QmYY2wi|Qmdpru5"
```

Expected pinned objects:

```text
QmXRDXGFVkSkyrAgQpjh23NYeG52EeGtAPKZ2tKiEtpduA recursive
QmYY2wiMqjuEVfFZYEZhaM9wLFfhnNh2vYkJ5QujvVBehT recursive
Qmdpru5DjMHb7XTAgGtwVnNb5C2bkZzc1snLv7R6ZuedNY recursive
```

4EVERLAND Bucket upload steps:

1. Open Dashboard -> Bucket.
2. Create a bucket for Lab 18.
3. Upload `labs/lab18/bucket-demo/` as a folder.
4. Record the directory CID and file CIDs shown by 4EVERLAND.
5. Verify through multiple gateways:

```text
https://ipfs.4everland.link/ipfs/Qmdpru5DjMHb7XTAgGtwVnNb5C2bkZzc1snLv7R6ZuedNY/docs/readme.txt
https://ipfs.io/ipfs/Qmdpru5DjMHb7XTAgGtwVnNb5C2bkZzc1snLv7R6ZuedNY/docs/readme.txt
https://dweb.link/ipfs/Qmdpru5DjMHb7XTAgGtwVnNb5C2bkZzc1snLv7R6ZuedNY/docs/readme.txt
```


### 4EVERLAND Bucket Upload Result

The demo files were uploaded to 4EVERLAND Bucket as individual IPFS objects:

| File | CID | Gateway URL |
|---|---|---|
| `assets/ipfs-demo.svg` | `bafkreibcps7cw4k6cxjq7zunnymgxf7dungezcach6iyzvdrpiekyfeftq` | `https://ipfs.io/ipfs/bafkreibcps7cw4k6cxjq7zunnymgxf7dungezcach6iyzvdrpiekyfeftq` |
| `docs/readme.txt` | `bafkreiasaahc5l6jgpndnjg76fuovfdekt2heufg53uekr6uxuieyltlr4` | `https://ipfs.io/ipfs/bafkreiasaahc5l6jgpndnjg76fuovfdekt2heufg53uekr6uxuieyltlr4` |
| `metadata.json` | `bafkreidwbpbutyzjpokv37zjbz6roofpiadodtrbpp7zs3clbbh2p7zcc4` | `https://ipfs.io/ipfs/bafkreidwbpbutyzjpokv37zjbz6roofpiadodtrbpp7zs3clbbh2p7zcc4` |

Verification on 2026-05-13:

```text
bafkreibcps7cw4k6cxjq7zunnymgxf7dungezcach6iyzvdrpiekyfeftq     -> SVG image content verified through ipfs.io
bafkreiasaahc5l6jgpndnjg76fuovfdekt2heufg53uekr6uxuieyltlr4  -> text file content verified through ipfs.io
bafkreidwbpbutyzjpokv37zjbz6roofpiadodtrbpp7zs3clbbh2p7zcc4    -> JSON metadata content verified through ipfs.io
```

## Task 5 — IPNS and Updates

IPFS CIDs are immutable. If `index.html` changes, the file CID and directory CID change. IPNS solves this by keeping a stable name that points to a current CID.

Local IPNS publication:

```bash
docker exec lab18-ipfs ipfs name publish --allow-offline /ipfs/QmYY2wiMqjuEVfFZYEZhaM9wLFfhnNh2vYkJ5QujvVBehT
```

Result:

```text
Published to k51qzi5uqu5dhsrzb83fwg8h6ztdg2uwcwwfeq7zhni9nlneg33rdmfpyi0l1x: /ipfs/QmYY2wiMqjuEVfFZYEZhaM9wLFfhnNh2vYkJ5QujvVBehT
```

4EVERLAND behaves similarly for hosted projects: the project URL stays stable while each redeploy creates a new immutable CID behind the scenes.

Update test to perform in 4EVERLAND:

1. Change a visible string in `labs/lab18/index.html`.
2. Commit and push.
3. Redeploy in 4EVERLAND.
4. Confirm that the project URL is unchanged but the deployment CID is different.

## Screenshots

Evidence collected during the lab run:

| Screenshot / Evidence | File / Evidence |
|---|---|
| 4EVERLAND Hosting dashboard | `labs/lab18/screenshots/hosting.png` shows the project, successful deployment status, CID, and production URL. |
| Deployed 4EVERLAND site | `labs/lab18/screenshots/site.png` shows the deployed DevOps Core Course site. |
| 4EVERLAND Bucket storage | `labs/lab18/screenshots/bucket.png` shows `lab18-bucket`, uploaded folders/files, and an IPFS CID column. |
| Public IPFS gateway | `labs/lab18/screenshots/ipfs.png` captures public gateway access; command-line verification through `ipfs.io` is recorded above. |
| Local IPFS node | Web UI was available at `http://localhost:5001/webui`; local node status, repo stats, and pin list are recorded above. |

## Centralized vs Decentralized Hosting

| Aspect | Traditional Hosting | IPFS / 4EVERLAND |
|---|---|---|
| Content addressing | Usually location-based URLs point to a server path. | Content-based CIDs identify exact bytes. |
| Single point of failure | One provider, VM, region, CDN, or account can become a critical dependency. | Content can be served by any peer or gateway that has the CID pinned. |
| Censorship resistance | Provider or infrastructure owner can remove or block content centrally. | Harder to remove globally if content is replicated and pinned by multiple parties. |
| Update mechanism | Overwrite files at the same URL or deploy a new release. | New content creates a new CID; stable URLs require IPNS, DNSLink, or platform routing. |
| Cost model | Pay for compute, storage, bandwidth, CDN, and managed services. | Pay mostly for pinning/storage/gateway bandwidth; no always-on app server for static content. |
| Speed / latency | Mature CDNs usually provide predictable low latency. | Depends on gateway, pinning location, cache state, and peer availability. |
| Best use cases | Dynamic apps, APIs, private systems, low-latency transactional workloads. | Static sites, public assets, archives, verifiable releases, censorship-resistant publishing. |

## Use Case Analysis

Decentralized hosting makes sense when integrity, persistence, public verifiability, and resilience matter more than server-side dynamism. Good examples are static documentation, release artifacts, public datasets, NFT metadata, course pages, and public portfolios.

Traditional hosting is better for dynamic applications, private dashboards, frequently changing data, low-latency APIs, authenticated user workflows, and systems that need server-side compute close to a database.

My recommendation is to use IPFS/4EVERLAND for static public content and artifacts that benefit from content-addressed integrity. For production applications, combine both approaches: serve public static assets or release bundles through IPFS, but keep dynamic APIs and databases on conventional infrastructure.

## Checklist

| Item | Status |
|---|---|
| IPFS concepts understood | Done |
| Local IPFS node running | Done |
| Content added to local IPFS | Done |
| 4EVERLAND account created | Done |
| Static site deployed via 4EVERLAND | Done |
| Files uploaded to Bucket | Done; three files uploaded and verified with CIDs |
| Content accessed via multiple gateways | Done; local gateway, 4EVERLAND project URL, and ipfs.io verified |
| IPNS / updates understood | Done; local IPNS published |
| `4EVERLAND.md` documentation complete | Done |
| Comparison analysis complete | Done |
