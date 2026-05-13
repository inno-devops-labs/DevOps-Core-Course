# Lab 17 — Cloudflare Workers Edge Deployment

# Deployment Summary

## Worker Information

* **Worker Name:** `edge-api`
* **Public URL:** `https://edge-api.dmayorov.workers.dev`
* **Runtime:** Cloudflare Workers
* **Language:** TypeScript
* **Deployment Platform:** Cloudflare Global Edge Network

---

## Screenshot — Successful Worker Deployment

![1](/docs_lab17/1.png)
![2](/docs_lab17/2.png)
![3](/docs_lab17/3.png)
![4](/docs_lab17/4.png)
![4-1](/docs_lab17/9.png)
---

# Main Routes

| Route      | Description                      |
| ---------- | -------------------------------- |
| `/`        | General application information  |
| `/health`  | Health check endpoint            |
| `/meta`    | Returns Cloudflare edge metadata |
| `/counter` | KV-backed persistent counter     |
| `/secrets` | Verifies secret configuration    |

---

## Screenshot — Worker Endpoints

### browser output for `/`
![6](/docs_lab17/6.png)

### browser output for `/health`
![7](/docs_lab17/7.png)

### browser output for `/meta`
![8](/docs_lab17/8.png)

### browser output for `/counter`
![9](/docs_lab17/14.png)


---

# Configuration Used

## Plaintext Variables

Configured in `wrangler.jsonc`:

```json
"vars": {
  "APP_NAME": "edge-api",
  "COURSE_NAME": "DevOps Core"
}
```

Plaintext variables are useful for non-sensitive configuration values, but they are not suitable for secrets because they are stored directly in the configuration file.


---

# Secrets

Configured using Wrangler CLI:

* `API_TOKEN`
* `ADMIN_EMAIL`

Secrets were securely stored using Cloudflare Workers secrets and were not committed to Git.

---

## Screenshot — Wrangler Secrets

![10](/docs_lab17/10.png)

---

# Workers KV Persistence

A KV namespace named `SETTINGS` was created and bound to the Worker.

The KV namespace stores a persistent counter value used by the `/counter` endpoint.

---

# Edge Metadata Example

Example response from `/meta` endpoint:

![12](/docs_lab17/12.png)

This demonstrates that Cloudflare Workers executes requests on Cloudflare’s edge network and provides request metadata from the edge location handling the request.

---

# Global Edge Distribution

Cloudflare Workers automatically distributes execution globally across Cloudflare edge locations.

Unlike traditional VM or Kubernetes deployments, there is no need to manually select deployment regions or configure regional replicas. Cloudflare automatically executes requests close to the client.

This removes operational complexity related to:

* multi-region deployments,
* failover,
* replication,
* and load balancing.

---

# Routing Concepts

## workers.dev

`workers.dev` provides an automatically generated public URL for a Worker.

Example:

```text
https://edge-api.dmayorov.workers.dev
```

## Routes

Routes attach Workers to traffic for existing Cloudflare-managed domains.

## Custom Domains

Custom Domains allow a Worker to directly serve traffic for a domain or subdomain.

---

# Persistence Verification

The `/counter` endpoint uses Workers KV to persist state across deployments.

Example:

```json
{ "visits": 15 }
```

```json
{ "visits": 16 }
```

```json
{ "visits": 17 }
```

![13](/docs_lab17/15.png)


After redeploying the Worker, the counter value remained persisted:

```json 
{ "visits": 19 }
```

![14](/docs_lab17/16-redeploy.png)
![15](/docs_lab17/17-after_redeploy.png)


This confirms that Workers KV persists data independently from Worker deployments.

---

# Observability & Operations

# Logs

Logs were inspected using:

```bash id="xkq2e9"
npx wrangler tail
```

Example log entry:

![16](/docs_lab17/18.png)

# Metrics

Metrics were reviewed in the Cloudflare Dashboard.

Observed metrics included:

* request count,
* successful requests,
* execution metrics,
* and CPU usage.

These metrics help monitor Worker performance and operational health.

---

## Cloudflare Dashboards

### Overview
![17](/docs_lab17/19.png)

### Metrics
![18](/docs_lab17/20.png)

### Observability
![19](/docs_lab17/21.png)

---

# Deployments & Rollbacks

Deployment history was viewed using:

```bash 
npx wrangler deployments list
```

Rollback functionality is available using:

```bash
npx wrangler rollback
```

Multiple Worker versions were deployed during development and testing.

---

## Screenshot — Deployment History

![20](/docs_lab17/22.png)
![21](/docs_lab17/23.png)
![22](/docs_lab17/24.png)
![23](/docs_lab17/25.png)

---

# Kubernetes vs Cloudflare Workers Comparison

| Aspect                    | Kubernetes                  | Cloudflare Workers          |
| ------------------------- | --------------------------- | --------------------------- |
| Setup complexity          | High                        | Low                         |
| Deployment speed          | Moderate                    | Very fast                   |
| Global distribution       | Manual multi-region setup   | Automatic edge distribution |
| Cost for small apps       | Higher                      | Very low                    |
| State/persistence model   | PVCs and databases          | KV and edge storage         |
| Control/flexibility       | Very high                   | More constrained            |
| Infrastructure management | Required                    | Fully managed               |
| Best use case             | Complex distributed systems | Lightweight edge APIs       |

---

# When to Use Each

## Kubernetes is better for:

* containerized systems,
* long-running services,
* advanced orchestration,
* and infrastructure-level control.

## Cloudflare Workers is better for:

* lightweight APIs,
* edge processing,
* globally distributed services,
* and low-latency workloads.

---

# Reflection

## What felt easier than Kubernetes?

* simpler deployment,
* no cluster setup,
* no container management,
* automatic HTTPS,
* automatic global distribution.

## What felt more constrained?

* no Docker containers,
* limited runtime environment,
* less infrastructure control,
* different persistence model.

## What changed because Workers is not a Docker host?

The application had to be adapted specifically for the Workers runtime.

Unlike Kubernetes:

* there are no containers,
* no pod networking,
* no persistent local filesystem,
* and no long-running processes.

Instead, the Worker relies on:

* event-driven execution,
* KV persistence,
* and Cloudflare-managed infrastructure.

---
