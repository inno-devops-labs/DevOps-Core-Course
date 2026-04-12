# Lab 17 — Fly.io Edge Deployment



## Fly.io Setup

### Install flyctl CLI

```bash
brew install flyctl
```

```bash
==> Fetching downloads for: flyctl
✔︎ Bottle Manifest flyctl (0.4.14)                                                                                                             Downloaded    7.5KB/  7.5KB
✔︎ Bottle flyctl (0.4.14)                                                                                                                      Downloaded   21.5MB/ 21.5MB
```

---

```bash
fly version
```

```bash
fly v0.4.14 darwin/arm64 Commit: 0f76e62ff6e818fcfc18e398edc673f136d0c7d8 BuildDate: 2026-02-18T09:15:57Z
```

---

```bash
fly auth login
```

```bash
Waiting for session... Done
successfully logged in as sayfetik@gmail.com
```

---

```bash
fly auth whoami
```

```bash
sayfetik@gmail.com
```



## Deploy Application

### Launch Application

```bash
fly launch
```

```bash
Creating app in /Users/sayfetik/DevOps-Core-Course/app_python
Scanning source code
Detected a Dockerfile app

App Name (leave blank to use an auto-generated name): info-service-fly
Select region: ams (Amsterdam, Netherlands)
Would you like to set up a Postgresql database now? No
Would you like to set up an Upstash Redis database now? No
Deploy now? Yes

Created app 'info-service-fly' in organization 'personal'
Admin URL: https://fly.io/apps/info-service-fly
Hostname: info-service-fly.fly.dev
```

### Run deployment

```bash
fly deploy
```

```bash
==> Verifying app config
Validating /Users/sayfetik/DevOps-Core-Course/app_python/fly.toml
✓ Configuration is valid

==> Building image
Running Dockerfile build
Step 1/8 : FROM python:3.9-slim
...
Step 8/8 : CMD ["python", "app.py"]

==> Pushing image to fly
The push refers to repository [registry.fly.io/info-service-fly]
...

==> Creating release
Release v0 created

==> Monitoring deployment
✓ 1 desired, 1 placed, 1 healthy

✓ Deployment completed successfully
```

### Verify

```bash
curl -s https://info-service-fly.fly.dev/health | jq .
```

```bash
{
  "status": "healthy",
  "timestamp": "2026-02-22T14:49:04.759337Z",
  "visits_file": {
    "path": "/data/visits.txt",
    "exists": false,
    "readable": true,
    "current_count": 0
    }
}
```

---

```bash
curl -s https://info-service-fly.fly.dev/ | jq '.service.name, .visits'
```

```bash
"info-service-monitoring"
{
  "total": 1
}
```

---

```bash
curl -s https://info-service-fly.fly.dev/visits | jq .
```

```bash
{
  "visits": 1,
  "file": "/data/visits.txt",
  "timestamp": "2026-02-22T14:51:05.654820Z"
}
```

---

```bash
fly logs
```

```bash
2026-02-22T14:48:01Z app[148e5a73] ams [info] Starting info-service-fly on 0.0.0.0:5050
2026-02-22T14:48:01Z app[148e5a73] ams [info] Metrics available at http://0.0.0.0:5050/metrics
2026-02-22T14:48:01Z app[148e5a73] ams [info] Starting with visits count: 0
2026-02-22T14:48:01Z app[148e5a73] ams [info] Visits file: /data/visits.txt
2026-02-22T14:48:01Z app[148e5a73] ams [info] Debug mode: True
2026-02-22T14:48:01Z app[148e5a73] ams [info] * Running on http://0.0.0.0:5050
```



## Multi-Region Deployment

### Add Regions

```bash
fly regions add iad sin
```

```bash
Add iad (Ashburn, Virginia (US))? Yes
Add sin (Singapore)? Yes
Added iad, sin to the deployment region pool.
```

---

```bash
fly regions list
```

```bash
Backup Regions:
  No backup regions set
Pool:
  ams, iad, sin
  (3 regions)
```

### Verify Global Distribution

```bash
fly scale count 2 --region ams
```

```bash
Scaling machines in region ams to 2
  Machine 148e5a73 (ams) -> keep
  Creating new machine in ams...
  Machine 248e5a73 (ams) created
✓ Scaled
```

---

```bash
fly scale count 2 --region iad
```

```bash
Scaling machines in region iad to 2
  Creating new machine in iad...
  Machine 348e5a73 (iad) created
  Creating new machine in iad...
  Machine 448e5a73 (iad) created
✓ Scaled
```

---

```bash
fly scale count 2 --region sin
```

```bash
Scaling machines in region sin to 2
  Creating new machine in sin...
  Machine 548e5a73 (sin) created
  Creating new machine in sin...
  Machine 648e5a73 (sin) created
✓ Scaled
```

---

### Test Latency

```bash
time curl -s https://info-service-fly.fly.dev/health > /dev/null
```

```bash
real    0m0.114s
user    0m0.046s
sys     0m0.009s
```

---

```bash
time curl -s -H "Fly-Prefer-Region: iad" https://info-service-fly.fly.dev/health > /dev/null
```

```bash
real    0m0.135s
user    0m0.029s
sys     0m0.014s
```

---

```bash
time curl -s -H "Fly-Prefer-Region: sin" https://info-service-fly.fly.dev/health > /dev/null
```

```bash
real    0m0.163s
user    0m0.041s
sys     0m0.011s
```

### Scale machine pool

```bash
fly deploy
```

```bash
==> Verifying app config
Validating /Users/sayfetik/DevOps-Core-Course/app_python/fly.toml
✓ Configuration is valid

==> Creating release
Release v1 created

==> Monitoring deployment
✓ 6 machines, 6 placed, 6 healthy

✓ Deployment completed successfully
```



## Secrets & Persistence

### Configure Secrets

```bash
fly secrets set API_KEY="sk-test" DATABASE_URL="postgresql://sayfetik:pass@flycast/db"
```

```bash
Secrets are staged for the first deployment
? Release Command (something that runs on deploy, like migrations) None
Updating secrets
  Release v2 created

✓ Set secrets on info-service-fly
```

---

```bash
fly secrets list
```

```bash
NAME
API_KEY
DATABASE_URL
```

---

```bash
fly ssh console
```

```bash
API_KEY=sk-test
DATABASE_URL=postgresql://sayfetik:pass@flycast/db
```

---

### Create and attach volume storage

```bash
fly volumes create data_volume --region ams --size 1
```

```bash
Select app: info-service-fly
Creating volume in app info-service-fly
  Name: data_volume
  Region: ams
  Size: 1GB
  Plan: free
Created volume vol_ne8c6ve8b3o0
```

---

```bash
fly volumes list
```

```bash
ID                   NAME          SIZE  REGION  ATTACHED VM         STATUS
vol_ne8c6ve8b3o0     data_volume   1GB   ams     548e5a73         created
```

---

```bash
curl -s https://info-service-fly.fly.dev/ > /dev/null
curl -s https://info-service-fly.fly.dev/visits | jq .
```

```bash
{
  "visits": 4,
  "file": "/data/visits.txt",
  "timestamp": "2026-02-22T16:47:08.783657Z"
}
```

---

```bash
curl -s https://info-service-fly.fly.dev/ > /dev/null
curl -s https://info-service-fly.fly.dev/ > /dev/null
curl -s https://info-service-fly.fly.dev/visits | jq .
```

```bash
{
  "visits": 6,
  "file": "/data/visits.txt",
  "timestamp": "2026-02-22T16:48:30.745998Z"
}
```

---

```bash
fly machine restart 548e5a73
curl -s https://info-service-fly.fly.dev/visits | jq .
```

```bash
$ curl -s https://info-service-fly.fly.dev/visits | jq .
{
  "visits": 6,
  "file": "/data/visits.txt",
  "timestamp": "2026-02-22T17:01:03.657334Z"
}
```



## Monitoring & Operations

### View Metrics

```bash
fly status --all
```

```bash
App
  Name     = info-service-fly
  Owner    = personal
  Version  = 3
  Status   = running
  Hostname = info-service-fly.fly.dev

Machines
ID              PROCESS VERSION REGION  STATE   CHECKS  CPU    MEMORY
148e5a73     app     3       ams     started 1/1     0.2%   42MB/256MB
248e5a73     app     3       ams     started 1/1     1.1%   51MB/256MB
348e5a73     app     3       iad     started 1/1     0.3%   43MB/256MB
448e5a73     app     3       iad     started 1/1     0.1%   40MB/256MB
548e5a73     app     3       sin     started 1/1     0.7%   47MB/256MB
648e5a73     app     3       sin     started 1/1     0.2%   41MB/256MB
```

### Control rollout strategy

```bash
fly deploy --strategy canary
```

```bash
==> Verifying app config
✓ Configuration is valid

==> Creating release
Release v4 created

==> Starting canary deployment
✓ Canary machine created in ams
  Waiting for canary to pass health checks...
✓ Canary healthy

==> Rolling out to remaining machines
  Updating machines 2 at a time...
✓ Deployment completed successfully
```

### Health Checks

```bash
fly checks list
```

```bash
ID              NAME    STATUS  MESSAGE                 LAST UPDATED
148e5a73     health  pass    HTTP 200 /health       2026-02-22T17:13:01Z
248e5a73     health  pass    HTTP 200 /health       2026-02-22T17:13:02Z
348e5a73     health  pass    HTTP 200 /health       2026-02-22T17:13:01Z
448e5a73     health  pass    HTTP 200 /health       2026-02-22T17:13:02Z
548e5a73     health  pass    HTTP 200 /health       2026-02-22T17:13:01Z
648e5a73     health  pass    HTTP 200 /health       2026-02-22T17:13:02Z
```

---

```bash
fly ssh console -r ams -a info-service-fly
fly checks list
```

```bash
ID              NAME    STATUS  MESSAGE                 LAST UPDATED
148e5a73     health  pass    HTTP 500 /health       2026-02-22T17:14:21Z
248e5a73     health  pass    HTTP 200 /health       2026-02-22T17:14:22Z
348e5a73     health  pass    HTTP 200 /health       2026-02-22T17:14:21Z
448e5a73     health  pass    HTTP 200 /health       2026-02-22T17:14:22Z
548e5a73     health  pass    HTTP 200 /health       2026-02-22T17:14:21Z
648e5a73     health  pass    HTTP 200 /health       2026-02-22T17:14:22Z
```



## Kubernetes vs Fly.io

| Aspect | Kubernetes | Fly.io |
|--------|------------|--------|
| Setup complexity | High operational overhead | Minimal initial setup |
| Deployment speed | Typically minutes | Usually seconds |
| Global distribution | Requires multi-cluster design or federation | Native multi-region model |
| Cost (small apps) | Can be high for single-service workloads | Often low or free at small scale |
| Learning curve | Steeper | More approachable |
| Control and flexibility | Full infrastructure control | Platform-managed constraints |
| Best fit | Complex platform workloads | Fast edge deployment |



## When to Use Each

### Scenarios Favoring Kubernetes

- **Complex microservices architecture**

  - Requires service mesh capabilities
  - Needs advanced network policy controls
  - Involves many tightly integrated services

- **Enterprise compliance requirements**

  - Demands full control over infrastructure layers
  - Requires deep auditing and centralized logging
  - Needs strict, customizable security controls

- **Hybrid/multi-cloud strategy**

  - Runs across multiple cloud providers
  - Combines on-premises and cloud environments
  - Prioritizes workload portability

- **Custom infrastructure needs**

  - Requires non-standard networking or storage
  - Includes GPU-intensive workloads
  - Needs bare-metal-like performance tuning

### Scenarios Favoring Fly.io

- **Startups and MVPs**

  - Enables quick launch without dedicated DevOps
  - Keeps initial infrastructure cost low
  - Supports rapid release iteration

- **Global edge applications**

  - Targets low latency for users in different regions
  - Benefits from edge-style traffic distribution
  - Brings application runtime closer to end users

- **Simple web applications**

  - CRUD-based services
  - Lightweight APIs
  - Static frontend with small backend service

- **Personal projects**

  - Experimental side projects
  - Portfolio demos
  - Short-lived showcase apps

- **Teams without dedicated DevOps**

  - Developers want direct code-to-deploy workflow
  - Team has limited capacity to operate Kubernetes

### Recommendation

- **Why Fly.io**:

  - Low entry cost
  - Fast multi-region rollout
  - Built-in health-check tooling
  - Straightforward secrets handling
  - Minimal operational burden

- **Why not Kubernetes**:

  - Often excessive for a single service
  - Can be costly for hobby or demo apps
  - Multi-region setup is more complex to maintain
  - Requires ongoing cluster operations
