# Lab 17

## 1. Deployment Summary
- **Worker URL:** `https://edge-api.<YOUR_SUBDOMAIN>.workers.dev`
- **Main routes:** `/`, `/health`, `/edge`, `/counter`
- **Configuration:**
  - Plaintext vars: `APP_NAME`, `COURSE_NAME`
  - Secrets: `API_TOKEN`, `ADMIN_EMAIL`
  - KV Namespace: `COUNTERS` (binding `COUNTERS`)

## 2. Evidence
### Cloudflare Dashboard Screenshot
![](lab17screenshots/metrics%20dashboard.png)
![](lab17screenshots/general%20dashboard.png)

### `/edge` JSON Response

```bash
$ curl https://edge-api.ivanisakov568.workers.dev/edge
{"edge":{"colo":"ATL","country":"US","city":"Atlanta","asn":13213,"httpProtocol":"HTTP/2","tlsVersion":"TLSv1.3"},"timestamp":"2026-05-08T11:33:54.378Z"}
```

### Wrangler tail output

```bash
$ npx wrangler tail

 ⛅️ wrangler 4.90.0
───────────────────
Successfully created tail, expires at 2026-05-08T17:48:33Z
Connected to edge-api, waiting for logs...
GET https://edge-api.ivanisakov568.workers.dev/health - Ok @ 5/8/2026, 2:48:40 PM
  (log) [2026-05-08T11:48:40.407Z] GET /health | colo: ATL
GET https://edge-api.ivanisakov568.workers.dev/counter - Ok @ 5/8/2026, 2:48:46 PM
  (log) [2026-05-08T11:48:46.826Z] GET /counter | colo: ATL
^C
```

### Counter work

```bash
$ curl https://edge-api.ivanisakov568.workers.dev/counter
{"visits":1}vexell@vexell-ASUS-TUF-Gaming-F15-FX506HC-FX506HC:~/DevOps/DevOps-Core-Course/labs/edge-api$ curl https://edge-api.ivanisakov568.workers.dev/counter
{"visits":2}vexell@vexell-ASUS-TUF-Gaming-F15-FX506HC-FX506HC:~/DevOps/DevOps-Core-Course/labs/edge-api$ curl https://edge-api.ivanisakov568.workers.dev/counter
{"visits":3}

```

### Deployment list

```bash
$ npx wrangler deployments list

 ⛅️ wrangler 4.90.0
───────────────────
Created:     2026-05-08T11:31:35.403Z
Author:      ivanisakov568@yandex.ru
Source:      Upload
Message:     Automatic deployment on upload.
Version(s):  (100%) f6decb89-d7ce-4304-bbd7-607c8ff9bd4e
                 Created:  2026-05-08T11:31:35.403Z
                     Tag:  -
                 Message:  -

Created:     2026-05-08T11:43:19.727Z
Author:      ivanisakov568@yandex.ru
Source:      Secret Change
Message:     -
Version(s):  (100%) 12927b24-7df9-49a3-ab2f-08def142b5b9
                 Created:  2026-05-08T11:43:19.727Z
                     Tag:  -
                 Message:  -

Created:     2026-05-08T11:44:21.816Z
Author:      ivanisakov568@yandex.ru
Source:      Secret Change
Message:     -
Version(s):  (100%) 4b1de1a0-0af1-4a03-b57c-3d268fccf7dd
                 Created:  2026-05-08T11:44:21.816Z
                     Tag:  -
                 Message:  -

Created:     2026-05-08T11:47:36.667Z
Author:      ivanisakov568@yandex.ru
Source:      Unknown (deployment)
Message:     -
Version(s):  (100%) a7d8f38c-ac3b-49d3-b2ff-be9c54648c01
                 Created:  2026-05-08T11:47:35.645Z
                     Tag:  -
                 Message:  -

```

### Local and global deploy

![](lab17screenshots/local%20deploy.png)
![](lab17screenshots/wrangler%20deploy.png)


## 3. Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|---------------------|
| **Setup complexity** | High – need cluster, nodes, networking, ingress | Low – `npx wrangler deploy` |
| **Deployment speed** | Minutes (image build, pod rollout) | Seconds (global script distribution) |
| **Global distribution** | Manual: choose regions, manage replicas | Automatic: every Cloudflare PoP |
| **Cost (for small apps)** | Fixed cost per node/cluster; often >$20/mo | Free tier: 100k requests/day, generous KV |
| **State/persistence model** | Persistent volumes, databases, full filesystem | Limited: Workers KV, Durable Objects, R2 |
| **Control/flexibility** | Full OS control, any container, custom networking | Sandboxed runtime, limited API set |
| **Best use case** | Long-running services, microservices, complex state | Lightweight APIs, edge rendering, JAMstack backends |

## 4. When to Use Each
- Kubernetes: when you need full container orchestration, long‑running processes, databases, or complex network policies.

- Cloudflare Workers: for globally distributed, low‑latency APIs, personal projects, small‑scale backends, JAMstack applications, or tasks that benefit from running at the edge.

## 5. Reflection

Working with Cloudflare Workers was significantly easier than Kubernetes:
- Instant global deployment with a single command.
- No need to manage nodes, ingress controllers, or scaling.
- KV storage gave simple persistence without provisioning a database.

However, it felt more constrained:
- Not easy accessible from Russia
- No filesystem, limited execution time (30s CPU for free plan).
- Must work within the Web‑standard Fetch API, no direct TCP sockets.
- Debugging requires wrangler tail or dashboard, not a full shell.

