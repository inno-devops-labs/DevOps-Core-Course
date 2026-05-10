# Documentation

## Deployment summary

### Worker URL

[https://edge-api.v-levasheva.workers.dev](https://edge-api.v-levasheva.workers.dev)

### Main routes

/ for general app info
/health for health status
/edge for cloudflare edge metadata
/counter for a persistent KV-based request counter, which shows the number of visits
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

### Example log or metrics screenshot

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

