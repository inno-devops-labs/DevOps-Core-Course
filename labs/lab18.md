# Lab 18 — Decentralized Hosting with 4EVERLAND & IPFS

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Web3%20Infrastructure-blue)
![points](https://img.shields.io/badge/points-20-orange)
![type](https://img.shields.io/badge/type-Exam%20Alternative-purple)

> Deploy content to the decentralized web using IPFS and 4EVERLAND for permanent, censorship-resistant hosting.

## Overview

The decentralized web (Web3) offers an alternative to traditional hosting where content is stored across a distributed network rather than centralized servers. IPFS (InterPlanetary File System) is the foundation, and 4EVERLAND provides a user-friendly gateway to this ecosystem.

**This is an Exam Alternative Lab** — Complete both Lab 17 and Lab 18 to replace the final exam.

**What You'll Learn:**
- IPFS fundamentals and content addressing
- Decentralized storage concepts
- Pinning services and persistence
- 4EVERLAND hosting platform
- Centralized vs decentralized trade-offs

**Prerequisites:** Basic understanding of web hosting, completed Docker lab

**Tech Stack:** IPFS | 4EVERLAND | Docker | Content Addressing

**Provided Files:**
- `labs/lab18/index.html` — A beautiful course landing page ready to deploy

---

## Exam Alternative Requirements

| Requirement | Details |
|-------------|---------|
| **Deadline** | 1 week before exam date |
| **Minimum Score** | 16/20 points |
| **Must Complete** | Both Lab 17 AND Lab 18 |
| **Total Points** | 40 pts (replaces 40 pt exam) |

---

## Tasks

### Task 1 — IPFS Fundamentals (3 pts)

**Objective:** Understand IPFS concepts and run a local node.

**Requirements:**

1. **Study IPFS Concepts**
   - Content addressing vs location addressing
   - CIDs (Content Identifiers)
   - Pinning and garbage collection
   - IPFS gateways

2. **Run Local IPFS Node**
   - Use Docker to run IPFS node
   - Access the Web UI
   - Understand node configuration

3. **Add Content Locally**
   - Add a file to your local IPFS node
   - Retrieve the CID
   - Access via local gateway

<details>
<summary>💡 Hints</summary>

**IPFS Concepts:**
- **Content Addressing:** Files identified by hash of content, not location
- **CID:** Unique identifier derived from content hash (e.g., `QmXxx...` or `bafyxxx...`)
- **Pinning:** Marking content to keep it (prevent garbage collection)
- **Gateway:** HTTP interface to IPFS network

**Run IPFS with Docker:**
```bash
docker run -d --name ipfs \
  -p 4001:4001 \
  -p 8080:8080 \
  -p 5001:5001 \
  ipfs/kubo:latest

# Web UI at http://localhost:5001/webui
# Gateway at http://localhost:8080
```

**Add Content:**
```bash
# Create test file
echo "Hello IPFS from DevOps course!" > hello.txt

# Add to IPFS
docker exec ipfs ipfs add /hello.txt
# Returns: added QmXxx... hello.txt

# Access via gateway
curl http://localhost:8080/ipfs/QmXxx...
```

**Resources:**
- [IPFS Docs](https://docs.ipfs.tech/)
- [IPFS Concepts](https://docs.ipfs.tech/concepts/)

</details>

---

### Task 2 — 4EVERLAND Setup (3 pts)

**Objective:** Set up 4EVERLAND account and explore the platform.

**Requirements:**

1. **Create Account**
   - Sign up at [4everland.org](https://www.4everland.org/)
   - Connect with GitHub or wallet
   - Explore dashboard

2. **Understand Services**
   - Hosting: Deploy websites/apps
   - Storage: IPFS pinning
   - Gateway: Access IPFS content

3. **Explore Free Tier**
   - Understand limits and capabilities
   - Review pricing for reference

<details>
<summary>💡 Hints</summary>

**4EVERLAND Services:**
- **Hosting:** Deploy from Git repos, automatic builds
- **Bucket (Storage):** Upload files, get IPFS CIDs
- **Gateway:** Access content via 4everland.link

**Dashboard:**
- Projects: Your deployed sites
- Bucket: File storage
- Domains: Custom domain setup

**Free Tier Includes:**
- 100 deployments/month
- 5GB storage
- 100GB bandwidth

**Resources:**
- [4EVERLAND Docs](https://docs.4everland.org/)

</details>

---

### Task 3 — Deploy Static Content (4 pts)

**Objective:** Deploy a static site to 4EVERLAND.

**Requirements:**

1. **Use the Provided Static Site**
   - A course landing page is provided at `labs/lab18/index.html`
   - Review the HTML/CSS to understand the structure
   - You may customize it or create your own

2. **Deploy via 4EVERLAND**
   - Connect your GitHub repository
   - Configure build settings
   - Deploy to IPFS via 4EVERLAND

3. **Verify Deployment**
   - Access via 4EVERLAND URL
   - Access via IPFS gateway
   - Note the CID

4. **Test Permanence**
   - Understand that content with same hash = same CID
   - Make a change, redeploy, observe new CID

<details>
<summary>💡 Hints</summary>

**Provided Static Site:**
The course provides a beautiful landing page at `labs/lab18/index.html` that you can deploy. It includes:
- Modern responsive design
- Course curriculum overview
- Learning roadmap
- "Deployed on IPFS" badge

**Deployment Steps:**
1. Go to 4EVERLAND Dashboard → Hosting
2. Click "New Project"
3. Import from GitHub
4. Select your repository and branch
5. Configure:
   - Framework: None (static)
   - Build command: (leave empty for static)
   - Output directory: `labs/lab18` (or root if you moved the file)
6. Deploy

**Alternative: Create Your Own**
You can also create your own static site. Keep it simple:
```html
<!DOCTYPE html>
<html>
<head>
    <title>My DevOps Portfolio</title>
</head>
<body>
    <h1>Welcome to My DevOps Journey</h1>
    <p>Deployed on IPFS via 4EVERLAND</p>
</body>
</html>
```

**Access URLs:**
- 4EVERLAND: `https://your-project.4everland.app`
- IPFS Gateway: `https://ipfs.4everland.link/ipfs/CID`

</details>

---

### Task 4 — IPFS Pinning (4 pts)

**Objective:** Use 4EVERLAND's storage (Bucket) for IPFS pinning.

**Requirements:**

1. **Upload Files to Bucket**
   - Upload multiple files (images, documents, etc.)
   - Get CIDs for each file

2. **Create a Directory Structure**
   - Upload a folder with multiple files
   - Understand directory CIDs

3. **Access via Multiple Gateways**
   - Access your content via:
     - 4EVERLAND gateway
     - Public IPFS gateways (ipfs.io, dweb.link)
   - Understand gateway differences

4. **Verify Pinning**
   - Confirm content is pinned
   - Understand pinning vs local storage

<details>
<summary>💡 Hints</summary>

**Bucket Upload:**
1. Dashboard → Bucket
2. Create new bucket
3. Upload files or folders
4. Get CID from file details

**Multiple Gateways:**
```bash
# 4EVERLAND
https://ipfs.4everland.link/ipfs/QmXxx...

# IPFS.io
https://ipfs.io/ipfs/QmXxx...

# Cloudflare
https://cloudflare-ipfs.com/ipfs/QmXxx...

# DWeb.link
https://dweb.link/ipfs/QmXxx...
```

**Directory Upload:**
- Upload entire folder
- Get directory CID
- Access files: `gateway/ipfs/DirCID/filename`

**Pinning Importance:**
- Unpinned content may be garbage collected
- Pinning services keep content available
- Multiple pins = more redundancy

</details>

---

### Task 5 — IPNS & Updates (3 pts)

**Objective:** Understand mutable content with IPNS.

**Requirements:**

1. **Understand IPNS**
   - IPFS = immutable (content changes = new CID)
   - IPNS = mutable pointer to IPFS content
   - IPNS name stays same, content can change

2. **Explore 4EVERLAND Domains**
   - Custom domains for your deployment
   - How 4EVERLAND handles updates

3. **Update Deployment**
   - Make changes to your static site
   - Redeploy
   - Observe: same URL, new CID

<details>
<summary>💡 Hints</summary>

**IPFS vs IPNS:**
- **IPFS CID:** `QmXxx...` - changes when content changes
- **IPNS Name:** `/ipns/k51xxx...` - stays same, points to current CID

**4EVERLAND Handles This:**
- Your project URL stays constant
- Behind scenes, updates the IPNS pointer
- Users always get latest version

**Domain Configuration:**
1. Dashboard → Hosting → Your Project
2. Settings → Domains
3. Add custom domain or use provided subdomain

</details>

---

### Task 6 — Documentation & Analysis (3 pts)

**Objective:** Document your work and analyze decentralized hosting.

**Create `4EVERLAND.md` with:**

1. **Deployment Summary**
   - What you deployed
   - URLs (4EVERLAND and IPFS gateways)
   - CIDs obtained

2. **Screenshots**
   - 4EVERLAND dashboard
   - Deployed site
   - Bucket storage
   - Multiple gateway access

3. **Centralized vs Decentralized Comparison**

| Aspect | Traditional Hosting | IPFS/4EVERLAND |
|--------|---------------------|----------------|
| Content addressing | | |
| Single point of failure | | |
| Censorship resistance | | |
| Update mechanism | | |
| Cost model | | |
| Speed/latency | | |
| Best use cases | | |

4. **Use Case Analysis**
   - When decentralized hosting makes sense
   - When traditional hosting is better
   - Your recommendations

---

## Checklist

- [ ] IPFS concepts understood
- [ ] Local IPFS node running
- [ ] Content added to local IPFS
- [ ] 4EVERLAND account created
- [ ] Static site deployed via 4EVERLAND
- [ ] Files uploaded to Bucket
- [ ] Content accessed via multiple gateways
- [ ] IPNS/updates understood
- [ ] `4EVERLAND.md` documentation complete
- [ ] Comparison analysis complete

---

## Rubric

| Criteria | Points |
|----------|--------|
| **IPFS Fundamentals** | 3 pts |
| **4EVERLAND Setup** | 3 pts |
| **Static Deployment** | 4 pts |
| **IPFS Pinning** | 4 pts |
| **IPNS & Updates** | 3 pts |
| **Documentation** | 3 pts |
| **Total** | **20 pts** |

**Grading:**
- **18-20:** Excellent understanding, thorough deployment, insightful analysis
- **16-17:** Working deployment, good documentation
- **14-15:** Basic deployment, incomplete analysis
- **<14:** Incomplete deployment

---

## Resources

<details>
<summary>📚 IPFS Documentation</summary>

- [IPFS Docs](https://docs.ipfs.tech/)
- [IPFS Concepts](https://docs.ipfs.tech/concepts/)
- [Content Addressing](https://docs.ipfs.tech/concepts/content-addressing/)
- [IPNS](https://docs.ipfs.tech/concepts/ipns/)

</details>

<details>
<summary>🌐 4EVERLAND</summary>

- [4EVERLAND Docs](https://docs.4everland.org/)
- [Hosting Guide](https://docs.4everland.org/hosting/overview)
- [Bucket (Storage)](https://docs.4everland.org/storage/bucket)

</details>

<details>
<summary>🔗 Public Gateways</summary>

- [IPFS Gateway Checker](https://ipfs.github.io/public-gateway-checker/)
- [Gateway List](https://docs.ipfs.tech/concepts/ipfs-gateway/#gateway-providers)

</details>

---

**Good luck!** 🌐

> **Remember:** Decentralized hosting trades some convenience for resilience and censorship resistance. Content-addressed storage ensures integrity - the same content always has the same identifier.
