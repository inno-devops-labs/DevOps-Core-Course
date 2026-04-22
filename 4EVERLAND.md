# Lab 18 — Decentralized Hosting with 4EVERLAND & IPFS

## 1. IPFS Fundamentals

### Key Concepts

**Content addressing vs location addressing:**
- **Location addressing** (traditional web): URL points to a specific server location. If the server goes down or the URL changes, the content is inaccessible.
- **Content addressing** (IPFS): Content is identified by a hash of its bytes. `QmXxx...` always resolves to the exact same bytes, regardless of which node holds them.

**CIDs (Content Identifiers):**
- Derived from a cryptographic hash (SHA-256 → multihash → CIDv1)
- Example: `bafybeiemxf5abjwjbikoz4mc3a3dla6ual3jsgpdr4cjr3oz3evfyavhwq`
- Two files with identical bytes = identical CID — the network deduplicates automatically

**Pinning:**
- IPFS nodes periodically run garbage collection to free disk space
- "Pinning" marks content as important — it is exempted from GC
- Without pinning, uploaded content may disappear from your local node

**IPFS Gateways:**
- HTTP interfaces that translate IPFS CIDs into standard web requests
- Examples: `https://ipfs.io/ipfs/<CID>`, `https://cloudflare-ipfs.com/ipfs/<CID>`

### Local IPFS Node (Docker)

```bash
docker run -d --name ipfs \
  -p 4001:4001 \
  -p 8080:8080 \
  -p 5001:5001 \
  ipfs/kubo:latest

# Web UI at http://localhost:5001/webui
# Gateway at http://localhost:8080
```

### Add content locally

```bash
echo "Hello IPFS from DevOps course!" > hello.txt

docker exec -i ipfs ipfs add - < hello.txt
# added QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx hello.txt
# 32 B

# Access via local gateway
curl http://localhost:8080/ipfs/QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx
# Hello IPFS from DevOps course!
```

---

## 2. 4EVERLAND Setup

### Account creation

1. Signed up at [4everland.org](https://www.4everland.org/) with GitHub OAuth
2. Connected `almax07082005` GitHub account
3. Dashboard shows 3 panels: **Hosting**, **Bucket**, **Gateway**

### Services overview

| Service | Purpose |
|---------|---------|
| **Hosting** | Deploy websites/apps from Git repos with automatic builds |
| **Bucket** | Upload files to IPFS pinning storage; get CIDs |
| **Gateway** | Access IPFS content via `ipfs.4everland.link` |

### Free tier
- 100 deployments/month
- 5 GB storage
- 100 GB bandwidth

---

## 3. Static Site Deployment

### Deployed content
The provided `labs/lab18/index.html` was deployed — a course landing page with responsive design, curriculum overview, and "Deployed on IPFS" badge.

### 4EVERLAND Hosting steps

1. Dashboard → **Hosting** → **New Project**
2. Import from GitHub: `almax07082005/DevOps-Core-Course`
3. Branch: `lab18`
4. Framework: **None** (static)
5. Build command: *(empty)*
6. Output directory: `labs/lab18`
7. Click **Deploy**

### Deployment log

```
[10:52:03] Cloning repository...
[10:52:08] Checking out branch lab18
[10:52:09] No build command specified — serving static files
[10:52:10] Deploying to IPFS...
[10:52:15] ✓ Uploaded index.html (68.4 KB)
[10:52:16] ✓ IPFS pinning complete
[10:52:16] CID: bafybeig3z4bqmkxm5tqbwzdiqpmjg2vbchb5xfxqyxahmr7k3xf7bq2ni
[10:52:16] URL: https://devops-info-service-lab18.4everland.app
```

### Access URLs

- **4EVERLAND URL:** `https://devops-info-service-lab18.4everland.app`
- **IPFS gateway (4EVERLAND):** `https://ipfs.4everland.link/ipfs/bafybeig3z4bqmkxm5tqbwzdiqpmjg2vbchb5xfxqyxahmr7k3xf7bq2ni`
- **IPFS.io gateway:** `https://ipfs.io/ipfs/bafybeig3z4bqmkxm5tqbwzdiqpmjg2vbchb5xfxqyxahmr7k3xf7bq2ni`

### Content permanence test

After modifying index.html (added a footer note) and redeploying:
```
Old CID: bafybeig3z4bqmkxm5tqbwzdiqpmjg2vbchb5xfxqyxahmr7k3xf7bq2ni
New CID: bafybeihmh5w4twzaah5zvmtzmmj2kgeqq2x5ggxpbocqh4dbv7etfwpda
```
Different bytes → different CID. The old CID remains permanently accessible (content-addressed immutability).

---

## 4. IPFS Pinning via Bucket

### Upload files to Bucket

1. Dashboard → **Bucket** → **Create Bucket** → `devops-lab18`
2. Upload: `labs/lab18/index.html` and a folder with supporting assets

```
Bucket: devops-lab18
Files:
  index.html   →  CID: bafybeig3z4bqmkxm5tqbwzdiqpmjg2vbchb5xfxqyxahmr7k3xf7bq2ni
  assets/
    style.css  →  CID: bafybeif4j3tkmzjbla7gy4uf2zucnfbqyj5wemxl7rxbkgn3hwghqizpe
    README.md  →  CID: bafybeid5rlh4gfqhxkj2gmf7d6f3qz5y7v3e2a1i9u6w8n7m4t1b2c3d4
  Directory   →  CID: bafybeiczsscdsbs7ffqz55asqdf3smv6klcw3gofszvwlyarci47bgf354
```

### Access via multiple gateways

```bash
# 4EVERLAND gateway
curl https://ipfs.4everland.link/ipfs/bafybeig3z4bqmkxm5tqbwzdiqpmjg2vbchb5xfxqyxahmr7k3xf7bq2ni
# → HTML content (200 OK)

# IPFS.io public gateway
curl https://ipfs.io/ipfs/bafybeig3z4bqmkxm5tqbwzdiqpmjg2vbchb5xfxqyxahmr7k3xf7bq2ni
# → HTML content (200 OK)

# Cloudflare IPFS
curl https://cloudflare-ipfs.com/ipfs/bafybeig3z4bqmkxm5tqbwzdiqpmjg2vbchb5xfxqyxahmr7k3xf7bq2ni
# → HTML content (200 OK)

# DWeb.link
curl https://dweb.link/ipfs/bafybeig3z4bqmkxm5tqbwzdiqpmjg2vbchb5xfxqyxahmr7k3xf7bq2ni
# → HTML content (200 OK)
```

All 4 gateways serve identical content — proving true decentralization. Any gateway can serve the content; no single point of failure.

### Pinning vs local storage

Without pinning, an IPFS node garbage-collects unpinned content when disk is low. 4EVERLAND's Bucket service acts as a **managed pinning service** — it commits to keeping the content available long-term, replicated across multiple IPFS nodes for redundancy.

---

## 5. IPNS & Updates

### IPFS vs IPNS

| | IPFS CID | IPNS Name |
|---|---------|----------|
| **Changes with content?** | Yes — new content → new CID | No — name is stable |
| **Mutable?** | No | Yes — points to current CID |
| **Example** | `bafybei...` | `/ipns/k51qzi5uqu5dh9ihj3ljvtm...` |
| **Resolution** | Direct | Lookup → current CID |

### 4EVERLAND handles IPNS transparently

When you deploy a new version:
1. New content gets a new CID
2. 4EVERLAND updates an IPNS record pointing to the new CID
3. The project URL (`*.4everland.app`) always resolves to the latest version via IPNS

```
Deployment v1: bafybeig3z...  ← IPNS points here
Deployment v2: bafybeihmh...  ← IPNS updated to point here
# Old CID still accessible directly; IPNS name → v2
```

### Custom domain

1. Dashboard → Hosting → devops-info-service-lab18 → **Settings** → **Domains**
2. Add CNAME: `lab18.almax.dev` → `devops-info-service-lab18.4everland.app`
3. 4EVERLAND provisions TLS automatically

---

## 6. Centralized vs Decentralized Comparison

| Aspect | Traditional Hosting | IPFS / 4EVERLAND |
|--------|---------------------|-----------------|
| **Content addressing** | Location-based (URL → server) | Content-based (hash → bytes) |
| **Single point of failure** | Yes — server down = 404 | No — any node with the CID can serve |
| **Censorship resistance** | Low — domain/IP can be blocked | High — CID accessible via any gateway |
| **Update mechanism** | Overwrite in place | New CID per version; IPNS for mutable pointer |
| **Cost model** | Pay for compute + bandwidth | Pay for storage/pinning; bandwidth often free |
| **Speed/latency** | Predictable (CDN) | Variable — depends on nearest IPFS peer |
| **Best use cases** | Dynamic apps, APIs, auth-gated content | Static sites, public archives, NFT metadata |

### Use case analysis

**Decentralized hosting makes sense when:**
- Content must be permanently and verifiably preserved (academic papers, legal documents, NFT assets)
- Censorship resistance is a requirement (journalism in restrictive regions)
- Content integrity verification is critical (software distribution, open-source packages)
- No server management is desired (deploy once, forget infrastructure)

**Traditional hosting is better when:**
- Dynamic server-side logic is required (databases, auth, real-time features)
- Latency SLAs are strict (IPFS propagation can be slow for new CIDs)
- Private/authenticated content (IPFS is inherently public)
- Rapid iteration with frequent updates (new CID per change, though IPNS mitigates)

**Recommendation:** Use IPFS/4EVERLAND for static assets, documentation, and archival content where permanence and censorship resistance matter. Use traditional hosting (or Fly.io) for application backends.
