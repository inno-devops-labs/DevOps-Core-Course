# Lab 17 — Fly.io Edge Deployment

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Edge%20Computing-blue)
![points](https://img.shields.io/badge/points-20-orange)
![type](https://img.shields.io/badge/type-Exam%20Alternative-purple)

> Deploy your application globally on Fly.io's edge infrastructure and experience simplified cloud deployment.

## Overview

Fly.io is a platform for running applications close to users worldwide. Unlike Kubernetes which requires cluster management, Fly.io abstracts infrastructure away while still giving you control over deployment, scaling, and observability.

**This is an Exam Alternative Lab** — Complete both Lab 17 and Lab 18 to replace the final exam.

**What You'll Learn:**
- Edge computing concepts
- Platform-as-a-Service deployment
- Global application distribution
- Kubernetes vs PaaS trade-offs
- Modern deployment workflows

**Prerequisites:** Working Docker image from Lab 2

**Tech Stack:** Fly.io | flyctl CLI | Docker | Multi-region deployment

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

### Task 1 — Fly.io Setup (3 pts)

**Objective:** Set up Fly.io account and CLI.

**Requirements:**

1. **Create Account**
   - Sign up at [fly.io](https://fly.io)
   - No credit card required for free tier
   - Verify email

2. **Install flyctl CLI**
   - Install for your operating system
   - Authenticate with `fly auth login`
   - Verify with `fly version`

3. **Explore Platform Concepts**
   - Understand Fly Machines (VMs)
   - Understand Fly Volumes (persistent storage)
   - Understand Regions and edge deployment

<details>
<summary>💡 Hints</summary>

**Installation:**
```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows (PowerShell)
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

**Authentication:**
```bash
fly auth login
# Opens browser for authentication

fly auth whoami
# Verify logged in
```

**Free Tier Includes:**
- 3 shared-cpu-1x VMs (256MB RAM)
- 3GB persistent storage
- 160GB outbound bandwidth

**Resources:**
- [Fly.io Docs](https://fly.io/docs/)
- [Getting Started](https://fly.io/docs/getting-started/)

</details>

---

### Task 2 — Deploy Application (4 pts)

**Objective:** Deploy your application to Fly.io.

**Requirements:**

1. **Prepare Application**
   - Ensure Dockerfile works locally
   - Application should listen on port 8080 (or configure in fly.toml)

2. **Launch Application**
   - Run `fly launch` in your app directory
   - Configure app name and region
   - Review generated `fly.toml`

3. **Deploy**
   - Run `fly deploy`
   - Wait for deployment to complete
   - Access your application via provided URL

4. **Verify**
   - Test all endpoints work
   - Check application logs
   - Verify health checks pass

<details>
<summary>💡 Hints</summary>

**Launch Process:**
```bash
cd app_python  # or app_go

fly launch
# Follow prompts:
# - App name: your-unique-name
# - Region: select closest
# - Postgres/Redis: No (for now)
# - Deploy now: Yes
```

**fly.toml Configuration:**
```toml
app = "your-app-name"
primary_region = "ams"  # Amsterdam, or your choice

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[checks]
  [checks.health]
    type = "http"
    port = 8080
    path = "/health"
    interval = "10s"
    timeout = "2s"
```

**Useful Commands:**
```bash
fly status          # App status
fly logs            # View logs
fly open            # Open in browser
fly ssh console     # SSH into machine
```

</details>

---

### Task 3 — Multi-Region Deployment (4 pts)

**Objective:** Deploy your application to multiple regions worldwide.

**Requirements:**

1. **Add Regions**
   - Deploy to at least 3 regions (e.g., ams, iad, sin)
   - Understand region codes

2. **Verify Global Distribution**
   - Check machines in each region
   - Access from different regions if possible

3. **Test Latency**
   - Document response times from different regions
   - Understand how Fly routes requests to nearest region

4. **Scale Machines**
   - Scale to 2 machines in primary region
   - Understand scaling commands

<details>
<summary>💡 Hints</summary>

**Region Codes:**
- `ams` - Amsterdam
- `iad` - Virginia, USA
- `sin` - Singapore
- `syd` - Sydney
- `lhr` - London

**Adding Regions:**
```bash
# Add regions
fly regions add iad sin

# List regions
fly regions list

# Check machines
fly machines list
```

**Scaling:**
```bash
# Scale in specific region
fly scale count 2 --region ams

# Or modify fly.toml and deploy
```

**Verify Distribution:**
```bash
fly status
# Shows machines in each region

fly ping
# Test connectivity to regions
```

</details>

---

### Task 4 — Secrets & Persistence (3 pts)

**Objective:** Configure secrets and persistent storage.

**Requirements:**

1. **Configure Secrets**
   - Set at least 2 secrets using `fly secrets`
   - Verify secrets are available in application
   - Understand secret management on Fly

2. **Attach Volume** (if app needs persistence)
   - Create Fly Volume
   - Attach to application
   - Verify data persists across deployments

<details>
<summary>💡 Hints</summary>

**Secrets:**
```bash
# Set secrets
fly secrets set DATABASE_URL="postgres://..." API_KEY="secret123"

# List secrets (names only)
fly secrets list

# Secrets available as env vars in app
```

**Volumes:**
```bash
# Create volume
fly volumes create myapp_data --size 1 --region ams

# Update fly.toml
[mounts]
  source = "myapp_data"
  destination = "/data"

# Deploy
fly deploy
```

**Verify Persistence:**
```bash
fly ssh console
# Inside machine
cat /data/visits
```

</details>

---

### Task 5 — Monitoring & Operations (3 pts)

**Objective:** Monitor and manage your deployed application.

**Requirements:**

1. **View Metrics**
   - Access Fly.io dashboard
   - View CPU, memory, network metrics
   - Understand machine states

2. **Manage Deployments**
   - Deploy a new version
   - View deployment history
   - Understand rollback capability

3. **Health Checks**
   - Configure HTTP health checks
   - Verify health check execution
   - Understand failure behavior

<details>
<summary>💡 Hints</summary>

**Dashboard:**
- Visit https://fly.io/dashboard
- Select your app
- View Metrics, Machines, Volumes tabs

**Deployments:**
```bash
fly releases
# Shows deployment history

fly deploy --strategy rolling
# Rolling deployment

fly deploy --strategy immediate
# Immediate replacement
```

**Health Checks in fly.toml:**
```toml
[checks]
  [checks.health]
    type = "http"
    port = 8080
    path = "/health"
    interval = "10s"
    timeout = "2s"
    grace_period = "30s"
```

</details>

---

### Task 6 — Documentation & Comparison (3 pts)

**Objective:** Document deployment and compare with Kubernetes.

**Create `FLYIO.md` with:**

1. **Deployment Summary**
   - App URL
   - Regions deployed
   - Configuration used

2. **Screenshots**
   - Fly.io dashboard
   - Multi-region machines
   - Metrics view

3. **Kubernetes vs Fly.io Comparison**

| Aspect | Kubernetes | Fly.io |
|--------|------------|--------|
| Setup complexity | | |
| Deployment speed | | |
| Global distribution | | |
| Cost (for small apps) | | |
| Learning curve | | |
| Control/flexibility | | |
| Best use case | | |

4. **When to Use Each**
   - Scenarios favoring Kubernetes
   - Scenarios favoring Fly.io
   - Your recommendation

---

## Checklist

- [ ] Fly.io account created
- [ ] flyctl CLI installed and authenticated
- [ ] Application deployed successfully
- [ ] Multiple regions configured (3+)
- [ ] Secrets configured
- [ ] Persistence tested (if applicable)
- [ ] Health checks working
- [ ] Metrics accessible
- [ ] `FLYIO.md` documentation complete
- [ ] Kubernetes comparison documented

---

## Rubric

| Criteria | Points |
|----------|--------|
| **Setup** | 3 pts |
| **Deployment** | 4 pts |
| **Multi-Region** | 4 pts |
| **Secrets & Persistence** | 3 pts |
| **Monitoring** | 3 pts |
| **Documentation** | 3 pts |
| **Total** | **20 pts** |

**Grading:**
- **18-20:** Excellent global deployment, thorough comparison
- **16-17:** Working deployment, good documentation
- **14-15:** Basic deployment, missing regions or docs
- **<14:** Incomplete deployment

---

## Resources

<details>
<summary>📚 Fly.io Documentation</summary>

- [Fly.io Docs](https://fly.io/docs/)
- [flyctl Reference](https://fly.io/docs/flyctl/)
- [Fly Machines](https://fly.io/docs/machines/)
- [Fly Volumes](https://fly.io/docs/volumes/)

</details>

<details>
<summary>🌍 Regions</summary>

- [Available Regions](https://fly.io/docs/reference/regions/)
- [Region Selection](https://fly.io/docs/reference/scaling/#regions)

</details>

---

**Good luck!** ✈️

> **Remember:** Fly.io is great for global, low-latency applications. Kubernetes gives more control but requires more management. Choose the right tool for your use case.
