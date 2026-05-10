# Documentation

## Deployment summary

### Worker URL

[https://edge-api.v-levasheva.workers.dev](https://edge-api.v-levasheva.workers.dev)

### Main routes

/ for general app info
/health for health status
/edge for cloudflare edge metadata
/counter for a persistent KV-based request counter, which shows the number of visits for / route
/admin-check is for checking if the requester is an admin, it uses secrets API_TOKEN and ADMIN_EMAIL, and the requester should provide valid token and email in the request headers
and also there is "Not Found" response for non-existent route

### Configuration used

the worker was configured using wrangler.jsonc, which defines the worker name, entrypoint (src/index.ts), compatibility date, environment variables, and resource bindings. the project uses a TypeScript Worker template and includes an APP_NAME variable binding together with a COUNTER_KV KV namespace binding used for persistent storage in the /counter endpoint.

## Evidence

### Screenshot of Cloudflare dashboard

![](./../app_python/docs/screenshots/lab17-shots/dashboard.png)

### Example /edge JSON response

Firstly, the local testing of all endpoints (for the deployed /edge some info such as asn and httpProtocol were added):

![](./../app_python/docs/screenshots/lab17-shots/endpoints%20local.png)

And the /edge endpoint in the deployed worker:

![](./../app_python/docs/screenshots/lab17-shots/edge%20deployed.png)

### How Workers distributes execution globally?

cloudflare workers are automatically executed on cloudflare edge locations around the world, so requests are handled close to the user without manually selecting regions. unlike traditional VM or PaaS platforms where you often deploy separately to regions, workers use cloudflare’s global network automatically, so there is no separate “deploy to 3 regions” step.

### The difference between workers.dev, Routes, and Custom Domains

- workers.dev is the default public cloudflare subdomain automatically provided for testing and accessing workers

- routes are specific url endpoints that worker will provide access to 

- custom domains allow exposing the worker directly through an owned custom domain, not through a provided workers.dev

## Configuration, Secrets & Persistence

### Explain why plaintext vars are not suitable for secrets

variables I added: "APP_NAME" and "COURSE_NAME"

plaintext vars are not safe for secrets because they are stored in config and visible in repo and dashboard, so anyone can read them

### Secrets

I added 2 secrets: API_TOKEN and ADMIN_EMAIL. They are used in the /admin-check endpoint, where the requester can pass their access token and email and see if they can be authenticated as an admin.

```bash
(devops) fountainer@Veronicas-MacBook-Air edge-api % npx wrangler secret list
[
  {
    "name": "ADMIN_EMAIL",
    "type": "secret_text"
  },
  {
    "name": "API_TOKEN",
    "type": "secret_text"
  }
]
```

![](./../app_python/docs/screenshots/lab17-shots/secrets.png)

### Workers KV persistence

### Document what you stored and how you verified it

I stored the number of visits of the / endpoint. Each time / is visited, the counter increases by one, and visits value is updated. The value then can be accessed through the /visits endpoint.

The persistance verification:

![](./../app_python/docs/screenshots/lab17-shots/persistance.png)

## Observability & Operations

### Example log or metrics screenshot

Logs

![](./../app_python/docs/screenshots/lab17-shots/logs.png)

Metrics

![](./../app_python/docs/screenshots/lab17-shots/metrics.png)

I looked at errors, requests, and request duration metrics for all deployed versions for the last 24 hours.

requests: total of 192. this metrics shows how many http requests hit the Worker through all endpoints.

errors: 0 errors. it can be confusing since I intentially hit invalid endpoint such as https://edge-api.v-levasheva.workers.dev/smth a lot of times to get error: "Not Found", but the case was that the Worker does not count 404 responses as errors, the real errors that are considered are runtime failures, which I did not have.

request duration: 3.15 ms on average. this metric shows the latency - how much it takes to process a request and send back a response.

### Multiple Deployments

* I created about 10 deployments but put here last 2 for readability

```bash
(devops) fountainer@Veronicas-MacBook-Air edge-api % npx wrangler deployments list

 ⛅️ wrangler 4.90.0
Created:     2026-05-10T16:57:52.287Z
Author:      v.levasheva@innopolis.university
Source:      Unknown (deployment)
Message:     -
Version(s):  (100%) 4844c942-5e05-4199-999f-b54af219ed99
                 Created:  2026-05-10T16:48:11.805Z
                     Tag:  -
                 Message:  -

Created:     2026-05-10T17:01:05.875Z
Author:      v.levasheva@innopolis.university
Source:      Unknown (deployment)
Message:     -
Version(s):  (100%) 9f0c5465-b3c2-462d-b199-bb1a6dc23d9f
                 Created:  2026-05-10T17:01:03.267Z
                     Tag:  -
                 Message:  -
```

```bash
(devops) fountainer@Veronicas-MacBook-Air edge-api % npx wrangler rollback

 ⛅️ wrangler 4.90.0
───────────────────
├ Your current deployment has 1 version(s):
│
│ (100%) 9f0c5465-b3c2-462d-b199-bb1a6dc23d9f
│       Created:  2026-05-10T17:01:03.267267Z
│           Tag:  -
│       Message:  -
│
✔ Please provide an optional message for this rollback (120 characters max) … test rollback
│
├  WARNING  You are about to rollback to Worker Version 4844c942-5e05-4199-999f-b54af219ed99.
│ This will immediately replace the current deployment and become the active deployment across all your deployed triggers.
│ However, your local development environment will not be affected by this rollback.
│ Rolling back to a previous deployment will not rollback any of the bound resources (Durable Object, D1, R2, KV, etc).
│
│ (100%) 4844c942-5e05-4199-999f-b54af219ed99
│       Created:  2026-05-10T16:48:11.805042Z
│           Tag:  -
│       Message:  -
│
✔ Are you sure you want to deploy this Worker Version to 100% of traffic? … yes
Performing rollback...
│
╰  SUCCESS  Worker Version 4844c942-5e05-4199-999f-b54af219ed99 has been deployed to 100% of traffic.

Current Version ID: 4844c942-5e05-4199-999f-b54af219ed99
```

## Kubernetes vs Cloudflare Workers Comparison

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| Setup complexity | blalallallla | blaldlalsdklas |
| Deployment speed | | |
| Global distribution | | |
| Cost (for small apps) | | |
| State/persistence model | | |
| Control/flexibility | | |
| Best use case | | |

## When to Use Each

### Scenarios favoring Kubernetes

### Scenarios favoring Workers

### Your recommendation

## Reflection

### What felt easier than Kubernetes?

### What felt more constrained?

### What changed because Workers is not a Docker host?

