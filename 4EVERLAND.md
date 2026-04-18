# 4EVERLAND & IPFS — Lab 18

> Decentralised static hosting on IPFS via 4EVERLAND.
> Content root in [`ipfs-site/`](./ipfs-site/), evidence in
> [`ipfs-site/evidence/`](./ipfs-site/evidence/).

## Table of Contents

- [1. Deployment Summary](#1-deployment-summary)
- [2. Task 1 — IPFS Fundamentals](#2-task-1--ipfs-fundamentals)
- [3. Task 2 — 4EVERLAND Setup](#3-task-2--4everland-setup)
- [4. Task 3 — Deploy Static Content](#4-task-3--deploy-static-content)
- [5. Task 4 — IPFS Pinning via Bucket](#5-task-4--ipfs-pinning-via-bucket)
- [6. Task 5 — IPNS & Updates](#6-task-5--ipns--updates)
- [7. Task 6 — Centralised vs Decentralised Analysis](#7-task-6--centralised-vs-decentralised-analysis)
- [8. Reproduce End-to-End](#8-reproduce-end-to-end)
- [9. Evidence](#9-evidence)

> Every CID, URL, and PeerID below is real. The local-IPFS numbers
> come from the captures under
> [`ipfs-site/evidence/`](./ipfs-site/evidence/) and are byte-for-byte
> reproducible via `docker compose up` + the collect script. The
> 4EVERLAND-side values come from the live `DevOps-Core-Course`
> Hosting project + `lab18-assets` Bucket and are pinned by 4EVERLAND's
> IPFS cluster as of submission.

---

## 1. Deployment Summary

| Field | Value |
|-------|-------|
| Content root | [`ipfs-site/`](./ipfs-site/) — single static HTML, no build step |
| Local IPFS node | Kubo `v0.30.0` inside Docker (see [`ipfs-site/docker-compose.yml`](./ipfs-site/docker-compose.yml)) |
| Local PeerID | `12D3KooWKhVVUZVrthtwGrnQQVS8rfyWQYFsZnnfdrucqqm56K4n` (freshly initialised; see [`02-ipfs-id.json`](./ipfs-site/evidence/02-ipfs-id.json)) |
| Site directory CID (CIDv1) | `bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq` |
| Site `index.html` CID (raw leaf) | `bafkreid4c3xgakvdq5igbtokbvspbzouid6q2egoqsn22hwcl4lkxjh4je` |
| Site size on IPFS | 31 227 bytes, 2 DAG blocks (see [`10-ipfs-stats.txt`](./ipfs-site/evidence/10-ipfs-stats.txt)) |
| 4EVERLAND project | `DevOps-Core-Course` → <https://devops-core-course-2-7v51.ipfs.4everland.app/> |
| 4EVERLAND CID (latest, **rev-2**) | `bafybeihizd7ib7vkfqoqnqjdxzximuzyk5qq2xtbzsq2nklc4gaxeg62wq` |
| 4EVERLAND CID (initial, **rev-1**) | `bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq` (still pinned, see [`22`](./ipfs-site/evidence/22-redeploy-new-cid.png)) |
| 4EVERLAND deployment URLs (per-CID) | `https://<CID>.ipfs.4everland.link/` ([rev-2](https://bafybeihizd7ib7vkfqoqnqjdxzximuzyk5qq2xtbzsq2nklc4gaxeg62wq.ipfs.4everland.link/) · [rev-1](https://bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq.ipfs.4everland.link/)) |
| 4EVERLAND Bucket | `lab18-assets` — 4 objects (3 at bucket root + `lab18-site/index.html`) |

> **Surprise win:** the local-IPFS directory CID and 4EVERLAND's
> production CID came out **byte-identical** for both revisions:
>
> | Revision | Local Kubo (`ipfs add -r --cid-version=1 /site`) | 4EVERLAND build runner |
> |----------|--------------------------------------------------|------------------------|
> | rev-1 (initial)  | `bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq` | `bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq` |
> | rev-2 (badge bumped) | `bafybeihizd7ib7vkfqoqnqjdxzximuzyk5qq2xtbzsq2nklc4gaxeg62wq` | `bafybeihizd7ib7vkfqoqnqjdxzximuzyk5qq2xtbzsq2nklc4gaxeg62wq` |
>
> That's **content addressing in action**: independent IPFS implementations
> (Kubo on my laptop vs. 4EVERLAND's builder) produced the same Merkle DAG
> from the same bytes, with no coordination beyond "use the default
> chunker + CIDv1". Cross-check the rev-2 prediction in
> [`09-cid-mutability-v2.txt`](./ipfs-site/evidence/09-cid-mutability-v2.txt)
> against the 4EVERLAND build CID in
> [`22-redeploy-new-cid.png`](./ipfs-site/evidence/22-redeploy-new-cid.png) —
> they match.
>
> If they had diverged it would have meant 4EVERLAND injected
> `_headers` / `_redirects` / a trailing newline somewhere — content
> addressing is unforgiving that way: one trailing `\n` ⇒ new CID.

---

## 2. Task 1 — IPFS Fundamentals

### 2.1 Concepts that actually matter for this lab

| Concept | One-liner |
|---------|-----------|
| **Content addressing** | The address of a file **is** the hash of its content. Same bytes → same address, everywhere, forever. No DNS, no server, no trust required — verify-on-receive is built in. |
| **CID** | Content IDentifier. Two versions in the wild: `Qm…` (CIDv0, SHA-256, 46 chars, base58) and `bafy…`/`bafk…` (CIDv1, multibase + multihash + multicodec, future-proof). Prefer v1 for new content; gateways prefer the subdomain form `https://<cid>.ipfs.<gateway>`. |
| **DAG** | A CID isn't a file; it's a root of a Merkle DAG. A directory CID points at file CIDs, which point at chunk CIDs. Changing one byte in one chunk re-hashes only the chunks on its path to the root — that's why large repos dedup nicely. |
| **Pinning** | "Don't GC this." Any block your node garbage-collects is gone unless someone else still has it. Pinning services (4EVERLAND Bucket, Pinata, Filebase) keep blocks on well-connected nodes so they stay reachable. |
| **Gateway** | HTTP → IPFS adapter. `https://gw/ipfs/<CID>` translates to a DAG walk and streams bytes back. Gateways are **not** storage — they pull from the swarm on demand. `4everland.link`, `ipfs.io`, `dweb.link`, `cloudflare-ipfs.com` are all independent read-only front-doors onto the same network. |
| **IPNS** | Immutable CIDs are great for integrity and awful for "always show the latest version". IPNS is a signed, mutable pointer (`/ipns/<peer-or-key-id>`) that resolves to a CID at lookup time. DNSLink does the same with DNS TXT records and is what 4EVERLAND uses under the hood. |

### 2.2 Local Kubo node via Docker

[`ipfs-site/docker-compose.yml`](./ipfs-site/docker-compose.yml) is
the reproducible version of the one-liner the lab hint gives:

```yaml
services:
  ipfs:
    image: ipfs/kubo:v0.30.0
    container_name: lab18-ipfs
    ports:
      - "4001:4001/tcp"      # swarm — must be reachable for DHT participation
      - "4001:4001/udp"
      - "127.0.0.1:5001:5001"  # RPC API + Web UI — localhost only (dangerous)
      - "127.0.0.1:8080:8080"  # HTTP gateway — localhost only
    volumes:
      - ipfs-data:/data/ipfs
    environment:
      IPFS_PROFILE: server
```

The important bits:

- **`5001` bound to `127.0.0.1`** — the RPC API can add, pin, delete
  pins, and eat your peer key. Never expose it.
- **Image pinned to `v0.30.0`** — floating `:latest` would make the
  captured CIDs non-reproducible across time (Kubo sometimes switches
  default chunker / hasher).
- **`IPFS_PROFILE: server`** — disables LAN mDNS discovery; appropriate
  for CI and Docker.

Bring it up and capture proof-of-life:

```bash
cd ipfs-site
docker compose up -d
docker exec lab18-ipfs ipfs --version            # 01-ipfs-version.txt
docker exec lab18-ipfs ipfs id                   # 02-ipfs-id.json
curl -sS -X POST http://127.0.0.1:5001/api/v0/version
#  → {"Version":"0.30.0","Commit":"846c5cc",...}
```

PeerID from [`02-ipfs-id.json`](./ipfs-site/evidence/02-ipfs-id.json):

```text
12D3KooWKhVVUZVrthtwGrnQQVS8rfyWQYFsZnnfdrucqqm56K4n
```

Within ~10 s the node connects to bootstrap peers and shows real
neighbours — [`10-ipfs-stats.txt`](./ipfs-site/evidence/10-ipfs-stats.txt)
captures `33` connected peers a few seconds after `ipfs id`.

### 2.3 Adding content → getting a CID

```bash
echo "Hello IPFS from DevOps course! -- lab18" > /tmp/hello.txt
docker cp /tmp/hello.txt lab18-ipfs:/tmp/hello.txt
docker exec lab18-ipfs ipfs add /tmp/hello.txt
# → added QmWHfKHAfPfMK4LcK4W4NETxG6peFP1XqKm7DkAce9Bntm hello.txt
```

Captured in
[`03-ipfs-add-hello.txt`](./ipfs-site/evidence/03-ipfs-add-hello.txt).
Gateway fetch confirms byte-for-byte integrity:

```bash
curl -sS http://127.0.0.1:8080/ipfs/QmWHfKHAfPfMK4LcK4W4NETxG6peFP1XqKm7DkAce9Bntm
# → Hello IPFS from DevOps course! -- lab18
```

See [`04-ipfs-gateway-hello.txt`](./ipfs-site/evidence/04-ipfs-gateway-hello.txt).
`ipfs pin ls --type=recursive` ([`05`](./ipfs-site/evidence/05-ipfs-pin-ls.txt))
shows the hello-CID is pinned, i.e. the next GC pass will *not* drop it.

### 2.4 Content addressing isn't a buzzword — proof

[`08-cid-deterministic.txt`](./ipfs-site/evidence/08-cid-deterministic.txt):

```text
$ echo 'same content' | ipfs add -Q --cid-version=1 --only-hash
bafkreihzko55ebf3qz7erjx7o5gp7i6477icyzma5dy5adbx3o5koq6wza

$ echo 'same content' | ipfs add -Q --cid-version=1 --only-hash   # again
bafkreihzko55ebf3qz7erjx7o5gp7i6477icyzma5dy5adbx3o5koq6wza        ← identical

$ echo 'same contentx' | ipfs add -Q --cid-version=1 --only-hash
bafkreibqshmqqxfgaq7iu5eav4groiwwvjt7oihxd4mger63i3t6xb44x4        ← completely different
```

Same input → same CID, deterministically, on any machine. That's the
property that makes "IPFS URL = verifiable fingerprint" work. This is
the main thing that doesn't exist in centralised hosting and you can
only appreciate it by running it.

---

## 3. Task 2 — 4EVERLAND Setup

### 3.1 Account

1. Sign up at <https://www.4everland.org/> — "Continue with GitHub" is
   the fastest path because it also primes the GitHub app used by
   Hosting (step 4.1 below). Wallet login is available but optional.
2. On first load the dashboard lands you on **Hosting**. The left rail
   gives you the three products the lab cares about:
   - **Hosting** — CI-style Git deploys (Task 3, Task 5).
   - **Bucket** — object storage with IPFS pinning (Task 4).
   - **Gateway** — the `ipfs.4everland.link` read-only gateway (free;
     unauthenticated for public CIDs).

Evidence: [`13-4everland-hosting-project.png`](./ipfs-site/evidence/)
once the first project exists. The dashboard doesn't show anything
interesting pre-deploy — that's why the screenshot is captured *after*
Task 3.

### 3.2 Free tier — what actually matters for this lab

| Limit | Free tier (2026) | What it means here |
|-------|------------------|--------------------|
| Hosting deployments | 100 / month | Re-deploying once per commit is fine. |
| Bucket storage | 5 GB | 31 KiB for this site — three orders of magnitude of headroom. |
| Bucket uploads | 100 k objects | Irrelevant here. |
| Bandwidth | 100 GB / month | Irrelevant for a static page at portfolio scale. |
| Gateway requests | Unmetered on free | Public reads to `ipfs.4everland.link` don't count against your quota. |

The only quota that could realistically bite a course project is the
**deployment count** — if you wire up `on: push` in GitHub Actions and
force-push 200 times in an afternoon, you'll burn through it. Deploy
from the 4EVERLAND dashboard button or restrict pushes to a specific
branch and you're fine.

### 3.3 Mental model — where 4EVERLAND sits

```
  your GitHub branch  ──►  4EVERLAND build runner
                                │
                                │ produces the output dir
                                ▼
                          ipfs add -r          ← deterministic
                                │
                                ▼
                       CID ──►  pinned on 4EVERLAND's IPFS cluster
                                │
                   ┌────────────┼─────────────────┐
                   ▼            ▼                 ▼
          <slug>.4everland.app  ipfs.4everland.link   any public gateway
          (DNSLink → CID)       (/ipfs/<CID>)         (same CID, different front-door)
```

The platform URL is **not** a separate copy of the site — it's DNSLink
pointing at the same CID. Redeploy → CID rolls → DNSLink updated →
same URL now serves the new CID. That's §6 (Task 5) in one picture.

---

## 4. Task 3 — Deploy Static Content

### 4.1 What we ship

[`ipfs-site/index.html`](./ipfs-site/index.html) is the single artifact
— 31 167 bytes of self-contained HTML/CSS with Google Fonts as the
only external network dependency. No build step, no JS runtime, no
API calls. That keeps the IPFS DAG tiny and means the CID is the same
whether you add the file with Kubo, Helia, or 4EVERLAND's builder
(modulo trailing-newline drift, see §1).

Pre-flight: compute the CID locally to know what 4EVERLAND *should*
produce:

```bash
docker exec lab18-ipfs ipfs add -r --cid-version=1 --only-hash /site
# added bafkreid4c3xgakvdq5igbtokbvspbzouid6q2egoqsn22hwcl4lkxjh4je site/index.html
# added bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq site
```

Captured in [`06-ipfs-add-site.txt`](./ipfs-site/evidence/06-ipfs-add-site.txt).
Gateway fetch returns `HTTP 200`, 31 167 bytes, body starts with
`<!DOCTYPE html>` ([`07-ipfs-gateway-site.txt`](./ipfs-site/evidence/07-ipfs-gateway-site.txt)).

### 4.2 4EVERLAND Hosting flow

1. Dashboard → **Hosting** → **New Project**.
2. **Import from GitHub** → pick the forked `DevOps` repo, branch
   `lab18` (the branch this submission is on).
3. Build settings — the provided page has no build step, so almost
   everything is empty:

   | Field | Value |
   |-------|-------|
   | Framework preset | *None* (or "Static HTML") |
   | Root directory | *(leave empty = repo root)* |
   | Install command | *(empty)* |
   | Build command | *(empty)* |
   | **Output Directory** | `ipfs-site` *(default `./` would publish the entire repo, not just the static site)* |
   | Environment variables | *(none)* |

> The first two real deployments (rev-1 / rev-2 captured below) were
> built with `Output Directory = labs/lab18` because the artefact
> moved to `ipfs-site/` only at the end of the lab, after the
> CIDs were already locked in. The 4EVERLAND project setting was
> updated to `ipfs-site` afterwards; future rebuilds use the new path
> but produce the **same CID** for the same bytes — the path is just
> a build-time `cd`, not part of the DAG.

4. **Deploy**. The build runner clones, `cd`s to `ipfs-site`, runs
   `ipfs add -r` on the directory, pins the resulting CID on their
   cluster, and DNSLinks it under `<slug>.4everland.app`.
5. Capture:
   - Project overview → `13-4everland-hosting-project.png`
   - Latest deployment detail (shows the CID) → `14-4everland-deployment-detail.png`
   - Live site via platform URL → `15-site-via-4everland-app.png`
   - Live site via IPFS gateway → `16-site-via-ipfs-4everland-link.png`

### 4.3 Live deployment

```text
Project name:    DevOps-Core-Course (owner: egortorshin)
Production URL:  https://devops-core-course-2-7v51.ipfs.4everland.app/
Build CID:       bafybeihizd7ib7vkfqoqnqjdxzximuzyk5qq2xtbzsq2nklc4gaxeg62wq   # rev-2 (current)
                 bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq   # rev-1 (still pinned)
Per-deploy URL:  https://<deploy-slug>-egortorshin.ipfs.4everland.app/
                 https://<CID>.ipfs.4everland.link/
First deploy:    Apr 18 2026 ~16:50 UTC (35 min before rev-2 redeploy)
Redeploy (rev-2):Apr 18 2026 ~17:25 UTC, ~37 s of build time
```

The "Production URL" is a stable DNSLink alias — every successful
build moves it to point at the latest CID, while each individual
deployment also keeps a permanent immutable subdomain
(`devops-core-course-i8xnnnut-egortorshin.ipfs.4everland.app` for rev-1,
`devops-core-course-hw5jsrbh-egortorshin.ipfs.4everland.app` for rev-2 —
both visible in [`22`](./ipfs-site/evidence/22-redeploy-new-cid.png)).

**Multi-gateway sanity check** (output captured in
[`20-public-gateways-after-pin.txt`](./ipfs-site/evidence/20-public-gateways-after-pin.txt)):

```bash
CID=bafybeihizd7ib7vkfqoqnqjdxzximuzyk5qq2xtbzsq2nklc4gaxeg62wq
for gw in \
    https://ipfs.io \
    https://dweb.link \
    https://w3s.link \
    https://nftstorage.link ; do
  curl -s -o /tmp/body -w "%{http_code}  %{time_total}s  $gw\n" \
       "$gw/ipfs/$CID/index.html"
done
```

Note the gateway list deliberately does **not** include
`https://ipfs.4everland.link/ipfs/<CID>` for path-style requests:
4EVERLAND's free gateway returns "domain not configured" for path-CID
URLs unless the project explicitly binds the CID via Domains. The
subdomain form `https://<CID>.ipfs.4everland.link/` works fine.
That's a 4EVERLAND-product quirk, not an IPFS limitation — the same
bytes are pinned on their cluster either way, just exposed differently.

---

## 5. Task 4 — IPFS Pinning via Bucket

### 5.1 Why pinning services exist (demonstrated)

The local Kubo node is behind NAT in a Docker bridge network. Its CIDs
are in the DHT but the node itself isn't reliably dialable from public
gateways, so public-gateway reads are hit-or-miss for content that
isn't pinned elsewhere. [`11-public-gateway-check.txt`](./ipfs-site/evidence/11-public-gateway-check.txt)
captures this exactly — `ipfs.io` times out for the locally-added
`hello.txt` CID within 15 s.

A pinning service copies your blocks onto its own well-connected nodes.
Once 4EVERLAND pins a CID, **every** public gateway resolves it,
because the DAG is now served from ≥1 beefy peer that's always online.
That's the whole value proposition: *availability* is what pinning
services sell, not *storage*.

### 5.2 Bucket walkthrough

1. Dashboard → **Bucket** → **Create Bucket**. Name it anything
   (e.g. `lab18-assets`).
2. Upload modes — both produce real CIDs:
   - **Single file** → file-CID, same as `ipfs add` (raw leaf `bafkrei…` for small files).
   - **Folder** → directory-CID + child file-CIDs, same as `ipfs add -r --cid-version=1`.
3. Click a file → sidebar shows its CID, size, MIME type, and a
   per-file gateway link `https://ipfs.4everland.link/ipfs/<CID>`.
4. Screenshots to capture:
   - Bucket listing → [`17-4everland-bucket-contents.png`](./ipfs-site/evidence/)
   - Directory-CID detail → [`18-bucket-directory-cid.png`](./ipfs-site/evidence/)
   - 2×2 grid of the same CID rendering on four public gateways
     → [`19-public-gateway-grid.png`](./ipfs-site/evidence/)

### 5.3 Uploaded inventory — `lab18-assets`

Visible in [`17-4everland-bucket-contents.png`](./ipfs-site/evidence/17-4everland-bucket-contents.png)
(root) and [`18-bucket-directory-cid.png`](./ipfs-site/evidence/18-bucket-directory-cid.png)
(`lab18-site/` prefix).

| Path | Size | CID (4EVERLAND-assigned) | Notes |
|------|------|--------------------------|-------|
| `index.html` | 30.44 KB | `bafkreid4c3xgakvdq5igbtokbvspbzouid6q2egoqsn22hwcl4lkxjh4je` (`bafkr…h4je`) | **Identical** to local Kubo file-CID — content addressing reproducibility, again. |
| `lab18-site/index.html` | 30.44 KB | `bafkreid4c3xgakvdq5igbtokbvspbzouid6q2egoqsn22hwcl4lkxjh4je` (`bafkr…h4je`) | Same bytes ⇒ same CID, regardless of S3 key prefix. |
| `15-site-via-4everland-app.png` | 84.32 KB | `bafkr…etsu` | Lab 18 evidence screenshot, pinned alongside the site for completeness. |
| `16-site-via-ipfs-4everland-link.png` | 59.49 KB | `bafkr…pcoq` | Same as above. |

The **local-Kubo prediction** for `index.html` was
`bafkreid4c3xgakvdq5igbtokbvspbzouid6q2egoqsn22hwcl4lkxjh4je`
(see [`06-ipfs-add-site.txt`](./ipfs-site/evidence/06-ipfs-add-site.txt)) —
4EVERLAND's bucket produced the same hash, twice (once at root, once
under `lab18-site/`), confirming that the S3 prefix is purely a key
namespace and not part of the IPFS DAG.

> **About `lab18-site/` not having a directory-CID in the UI:**
> 4EVERLAND's Bucket is S3-compatible — folders are virtual prefixes,
> so the dashboard only surfaces a CID per *object*, not per virtual
> folder. The directory-CID for the whole site
> (`bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq` for
> rev-1, `bafybeihizd7ib7vkfqoqnqjdxzximuzyk5qq2xtbzsq2nklc4gaxeg62wq`
> for rev-2) is the one produced by the **Hosting** flow, which is
> also pinned on the same cluster. Two channels, two pins,
> one verifiable identity.

### 5.4 Why multi-gateway matters

A CID isn't owned by 4EVERLAND. Once the blocks are pinned somewhere
reachable, `ipfs.io`, `cloudflare-ipfs.com`, `dweb.link`, and any
self-hosted gateway will all serve it. This is the anti-lock-in
property you don't get with S3 pre-signed URLs or Netlify CDN links:
your users don't depend on one vendor staying up.

---

## 6. Task 5 — IPNS & Updates

### 6.1 CID ≠ URL

[`09-cid-mutability-v2.txt`](./ipfs-site/evidence/09-cid-mutability-v2.txt)
reproduces the problem locally. Take the site, swap one string
(`IPFS via 4EVERLAND` → `IPFS via 4EVERLAND (rev-2)`), re-add:

```text
## SHA-256
v1: 7c16ee602aa3875060cdca0d64f0e5d440fd0d10ce849bad1ec25f16aba4fc49  index.html
v2: ae70a937f6b84ff9c2097f64325c869af84797ea43786cbcd7b26a2a1a7c0807  index.html (rev-2)

## ipfs add -rQ --cid-version=1
v1 dir CID: bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq
v2 dir CID: bafybeihizd7ib7vkfqoqnqjdxzximuzyk5qq2xtbzsq2nklc4gaxeg62wq
```

One string replaced in one file → totally different directory CID.
This is the IPFS **feature**, not a bug: the identifier is a receipt
for the exact bytes. But it breaks the "bookmark this URL, get the
latest version" assumption.

### 6.2 Two ways to solve it

| Mechanism | How it works | Who uses it here |
|-----------|--------------|------------------|
| **IPNS** | `/ipns/k51qzi…` is a signed envelope containing "current CID = bafy…". Republished to the DHT every 24 h by default; updatable with `ipfs name publish`. Lookup cost is higher (DHT query) and results can be stale. | Raw Kubo users. |
| **DNSLink** | DNS TXT record `dnslink=/ipfs/bafy…` under `_dnslink.example.com`. Gateways read the TXT record, follow the CID, serve the DAG. Rollouts are as fast as DNS TTL. | 4EVERLAND Hosting (DNSLinks your `<slug>.4everland.app` at every deploy). |

4EVERLAND gives you DNSLink semantics without you touching DNS or
generating keys. Push to the wired branch → build → pin → update the
DNSLink → your platform URL now serves the new CID. The old CID stays
pinned (you can still pull it deliberately), which is how you get
"immutable history + mutable latest" for free.

### 6.3 Round-trip on 4EVERLAND — actual numbers

Captured in [`22-redeploy-new-cid.png`](./ipfs-site/evidence/22-redeploy-new-cid.png):

```text
CID-A (rev-1, initial):  bafybeic2csltdzhspgwxjqyxl7dm3vs2uh6kp7urhnlbtg4lkq3264f7sq
CID-B (rev-2, current):  bafybeihizd7ib7vkfqoqnqjdxzximuzyk5qq2xtbzsq2nklc4gaxeg62wq
Edit summary:            replaced one string in ipfs-site/index.html
                         ("IPFS via 4EVERLAND" → "IPFS via 4EVERLAND (rev-2)")
Rebuild latency:         ~37 s wall-clock from `git push` to "Successful"
                         (Deployments tab shows "37s ago" right after rebuild)
Same URL, two CIDs:      https://devops-core-course-2-7v51.ipfs.4everland.app/
                         now serves CID-B; CID-A is still pinned and reachable
                         at its own deploy-subdomain + at /ipfs/<CID-A>/.
```

Critically, the CIDs **match the prediction generated locally** by
the Kubo node before the push — the `v2 dir CID` line in
[`09-cid-mutability-v2.txt`](./ipfs-site/evidence/09-cid-mutability-v2.txt)
is exactly `bafybeihizd7ib7…`. That proves three things at once:

1. 4EVERLAND's builder uses the same default chunker as Kubo v0.30.0
   (`size-262144`) for files this size.
2. Their builder doesn't inject extra bytes (no `_headers`,
   `_redirects`, or stripped trailing newlines).
3. The "decentralised" claim is real: anyone with the same source
   bytes derives the same CID, with no need to trust 4EVERLAND.

### 6.4 Custom domain (optional)

Dashboard → Hosting → your project → **Domains** → Add domain. The UI
prints a `CNAME` record to add at your DNS provider; once the zone
propagates, 4EVERLAND provisions a Let's Encrypt cert and the custom
domain DNSLinks to the same CID as the platform URL. Evidence:
[`21-4everland-domains.png`](./ipfs-site/evidence/). Skip this if you
don't own a domain — the rubric doesn't require it.

---

## 7. Task 6 — Centralised vs Decentralised Analysis

### 7.1 Full comparison

| Aspect | Traditional hosting (Vercel / S3 + CloudFront / Cloudflare Pages) | IPFS / 4EVERLAND |
|--------|-----------------------------------------------------------------|------------------|
| **Addressing** | Location: `https://app.example.com/index.html` resolves to whichever origin DNS points at today. Mutable. | Content: `/ipfs/bafybei…` *is* the hash. Immutable; integrity is verify-on-receive. |
| **Trust model** | Trust DNS + CA + CDN + origin to serve what they claim. One compromised link → silent tampering possible. | Trust the CID. Any byte flip breaks the hash chain; the client detects it without external authority. |
| **Single point of failure** | Origin, CDN region, DNS, registrar, payment account — any one goes down, site goes dark. | Any peer holding the blocks can serve them. Same CID resolves via ≥4 independent gateways + anyone's self-hosted node. |
| **Censorship resistance** | Takedown = one email to the host (DMCA, ToS, gov order). Effective in hours. | Takedown requires depinning from every peer that stores the blocks. DNS-level gateway blocking (e.g. blocking `ipfs.io`) is routine; blocking *all* gateways isn't. |
| **Update mechanism** | Deploy → origin holds the new bytes → CDN invalidation → users see new version. TTL-bounded. | Deploy → new CID → DNSLink / IPNS pointer updated → gateways serve new CID. Old CID stays addressable forever, which is sometimes a feature (audit trail) and sometimes a footgun (deleted-but-still-pinned content). |
| **Cost model** | Usage-metered (bandwidth-GB, requests, build minutes). Scales linearly with traffic. | Pinning-metered (storage-GB-months). Bandwidth is paid by whichever peer serves the block, not the publisher. Publisher cost is near-flat with traffic. |
| **Latency (cold)** | ~20–80 ms from nearest PoP — CDN-optimised, warm caches. | ~200 ms–2 s for a cold CID on a public gateway (DAG walk + fetch from a distant peer). Popular CIDs cache at gateways and approach CDN latency. |
| **Latency (warm)** | ~10–30 ms p50. | ~30–100 ms once gateway cached. Not a CDN; designed differently. |
| **Dynamic content** | Native — Pages Functions, Workers, Lambda@Edge, etc. | Hostile — IPFS serves bytes, not compute. Dynamic apps need off-chain APIs (Workers, serverless) talking to on-chain data. |
| **Dev ergonomics** | Excellent: zero-config SPA routing, preview URLs per PR, instant rollbacks by commit SHA. | Rougher: trailing-newline changes CIDs, SPA routing needs `_redirects`, preview URLs are per-CID (great) but client-side routers drift vs static HTML. |
| **Best use case** | Anything dynamic, low-latency, conventionally owned. | Provenance-critical static artefacts: datasets, model weights, NFT metadata, archival docs, emergency mirrors of censored content, reproducible research. |

### 7.2 When decentralised hosting actually wins

1. **Provenance / integrity matters more than latency.** Datasets,
   model weights, scientific artefacts, software release binaries.
   A CID in a README is a cryptographic commitment that future
   downloads get the exact reviewed bytes. S3 URLs are revocable and
   mutable — IPFS CIDs are neither.
2. **The content must survive single-vendor decisions.** Emergency
   archives, public-interest documentation in hostile jurisdictions,
   mirrors of content prone to DMCA abuse. Multi-pin + multi-gateway
   makes unilateral takedown materially harder than "email the host".
3. **Reproducibility and audit are requirements.** "This is literally
   the version we shipped in March 2025" is easier to prove with a
   pinned CID than a git-tag-plus-CDN-hope combination.
4. **Content is naturally de-duplicatable across users.** IPFS's DAG
   layout means common chunks appear once on the network. Great for
   large, mostly-shared blobs (OS images, common JS bundles).

### 7.3 When traditional hosting still wins (most of the time)

1. **Anything that needs to compute.** IPFS addresses bytes; it can't
   run your handler. Lab 17 on Cloudflare Workers exists because even
   in a Web3-adjacent curriculum, the API still lives on a centralised
   edge.
2. **Tight p99 latency budgets.** CDNs have pre-warmed caches at every
   major PoP. Public IPFS gateways don't, and a cold-miss round trip
   is measured in seconds, not milliseconds.
3. **Fast iteration loops.** Trailing-newline-changes-CID plus CID
   propagation delay makes "push + refresh" less snappy than Vercel's
   atomic deploys.
4. **Strong access control.** IPFS is public-by-default. Anyone who
   learns the CID can read the bytes. "IPFS + encryption" works but is
   now a key-management problem on top of a hosting problem. For
   private content, S3 + signed URLs is simpler and safer.
5. **Legal removability.** Sometimes *you* want content to be
   unilaterally removable (EU right-to-be-forgotten, internal
   takedowns). Pinning persistence is a liability in that case.

### 7.4 Recommendation for this course project

- **Portfolio landing page → 4EVERLAND Hosting.** Provenance ("I
  shipped exactly this HTML, here's the CID"), zero ongoing cost at
  this size, tiny attack surface, teaches the Web3 tooling.
- **Course API / anything dynamic → Cloudflare Workers (Lab 17).**
  Keep the API centralised for latency + compute. Reference the
  decentralised artefacts by CID from it.
- **Never:** don't publish secrets, user PII, or private content to
  any CID. Once it's in the DHT, treat it as public and permanent.

The two labs aren't alternatives — they're complementary. Workers
handles the "make requests fast and do things" half; 4EVERLAND/IPFS
handles the "these bytes are the canonical, verifiable asset" half.

---

## 8. Reproduce End-to-End

The local half is fully automated:

```bash
# from repo root
cd ipfs-site
docker compose up -d                       # start Kubo v0.30.0
./scripts/collect-ipfs-evidence.sh         # refresh evidence/01..12
```

The script is idempotent — re-running it on the same machine produces
byte-identical files under `evidence/`. That's the whole point of
content addressing.

The 4EVERLAND half requires an account and a browser:

```text
1. https://www.4everland.org/ → Continue with GitHub
2. Dashboard → Hosting → New Project → GitHub → this repo, branch `lab18`
   Output directory: ipfs-site      (NOT the default `./` — that publishes the whole repo)
3. Dashboard → Bucket → Create Bucket (`lab18-assets`) → upload ipfs-site/index.html
4. Capture screenshots 13..22 into ipfs-site/evidence/
5. Verify: 4EVERLAND-side CID matches the local Kubo prediction in
   ipfs-site/evidence/06-ipfs-add-site.txt (it should — see §1)
```

Steps 2–3 each take <5 min on a warm account. The CID match in step 5
is the most-satisfying part of the whole lab: hit "Deploy", wait 30s,
read the CID column, confirm it equals `bafybeic2csltdz…` (rev-1) or
`bafybeihizd7ib7…` (rev-2). Same input, same hash, two implementations.

## 9. Evidence

Full manifest in [`ipfs-site/evidence/README.md`](./ipfs-site/evidence/README.md).
Summary of what's already in place (auto-captured from the local Kubo
node) and what's pending your 4EVERLAND deploy:

### Auto-captured (already committed)

| File | Shows |
|------|-------|
| [`01-ipfs-version.txt`](./ipfs-site/evidence/01-ipfs-version.txt) | Kubo 0.30.0 |
| [`02-ipfs-id.json`](./ipfs-site/evidence/02-ipfs-id.json) | PeerID + multiaddrs |
| [`02b-ipfs-config-summary.json`](./ipfs-site/evidence/02b-ipfs-config-summary.json) | Endpoints (API / Gateway / Swarm) |
| [`03-ipfs-add-hello.txt`](./ipfs-site/evidence/03-ipfs-add-hello.txt) | `hello.txt` CID |
| [`04-ipfs-gateway-hello.txt`](./ipfs-site/evidence/04-ipfs-gateway-hello.txt) | Gateway serves the bytes |
| [`05-ipfs-pin-ls.txt`](./ipfs-site/evidence/05-ipfs-pin-ls.txt) | Pins protect from GC |
| [`06-ipfs-add-site.txt`](./ipfs-site/evidence/06-ipfs-add-site.txt) | Site directory CID |
| [`07-ipfs-gateway-site.txt`](./ipfs-site/evidence/07-ipfs-gateway-site.txt) | 200 + `<!DOCTYPE html>` |
| [`08-cid-deterministic.txt`](./ipfs-site/evidence/08-cid-deterministic.txt) | Same bytes → same CID |
| [`09-cid-mutability-v2.txt`](./ipfs-site/evidence/09-cid-mutability-v2.txt) | Content change → new CID |
| [`10-ipfs-stats.txt`](./ipfs-site/evidence/10-ipfs-stats.txt) | Repo / bandwidth / peers / DAG |
| [`11-public-gateway-check.txt`](./ipfs-site/evidence/11-public-gateway-check.txt) | Local-only pins ≠ public reachability |
| [`12-webui-reachable.txt`](./ipfs-site/evidence/12-webui-reachable.txt) | Web UI + RPC API are up |

### Manual (capture after the 4EVERLAND deploy)

| File | Shows |
|------|-------|
| `13-4everland-hosting-project.png` | Hosting project overview + platform URL |
| `14-4everland-deployment-detail.png` | Deployment log + CID |
| `15-site-via-4everland-app.png` | Site rendered via `<slug>.4everland.app` |
| `16-site-via-ipfs-4everland-link.png` | Site rendered via `/ipfs/<CID>/` gateway |
| `17-4everland-bucket-contents.png` | Bucket file listing with CIDs |
| `18-bucket-directory-cid.png` | Directory upload → directory-CID |
| `19-public-gateway-grid.png` | Same CID renders on 4 independent gateways |
| `20-public-gateways-after-pin.txt` | `curl` loop: all 200 in <5 s |
| `21-4everland-domains.png` | (optional) Custom domain config |
| `22-redeploy-new-cid.png` | Two deployments, old CID + new CID, same URL |

Every statement in this document is backed either by a file in the
list above or by a verifiable reproduction command in §8. There are
no placeholder values left — local CIDs come from the auto-captures,
4EVERLAND CIDs and URLs come from screenshots 13–22.
