# Lab 17 — Cloudflare Workers Edge Deployment

## Deployment Summary

### Worker Information

- **Worker Name:** `edge-api`
- **Public URL:** `https://edge-api.kvassoedik.workers.dev`

### Implemented Routes

| Route | Description |
|---|---|
| `/` | General application information |
| `/health` | Health check endpoint |
| `/edge` | Edge metadata from Cloudflare runtime |
| `/config` | Environment variables and secrets status |
| `/counter` | Persistent KV-backed counter |

### Technologies Used

- Cloudflare Workers
- Wrangler CLI
- TypeScript
- Workers KV
- workers.dev deployment
- Git version control

## Task 1 — Cloudflare Setup

### Wrangler Authentication

The Wrangler CLI was authenticated successfully using OAuth login.

#### Commands Used

```bash
npx wrangler login
npx wrangler whoami
```

#### Verification Output

```text
You are logged in with an OAuth Token, associated with the email kvassoedik@gmail.com.
```

#### Project Structure

The generated Worker project contains:

| File | Purpose |
|---|---|
| `src/index.ts` | Main Worker source code |
| `wrangler.jsonc` | Worker configuration |
| `package.json` | Dependencies and scripts |

## Task 2 — Build and Deploy a Worker API

### Local Development

The Worker was started locally using:

```bash
npx wrangler dev
```

#### Local Testing

The following endpoints were tested locally:

```bash
curl http://localhost:8787/
curl http://localhost:8787/health
curl http://localhost:8787/edge
curl http://localhost:8787/config
curl http://localhost:8787/counter
```

#### Local Responses

```
{"app":"edge-api","course":"devops-core","message":"Hello from Cloudflare Workers","routes":["/","/health","/edge","/config","/counter"],"timestamp":"2026-05-14T17:49:59.543Z"}{"status":"ok","runtime":"cloudflare-workers","timestamp":"2026-05-14T17:49:59.576Z"}{"colo":"HEL","country":"FI","city":"Helsinki","asn":26383,"httpProtocol":"HTTP/1.1","tlsVersion":"TLSv1.3"}{"appName":"edge-api","courseName":"devops-core","adminEmailConfigured":false,"apiTokenConfigured":false,"note":"Secret values are not returned."}{"visits":1,"persistedIn":"Workers KV"}{"visits":2,"persistedIn":"Workers KV"}
```

### Deployment

#### Deploy Command

```bash
npx wrangler deploy
```

#### Deployment Output

```text
Deployed edge-api triggers
https://edge-api.kvassoedik.workers.dev
```

#### Public Endpoint Verification

The deployed Worker was tested successfully using:

```bash
curl https://edge-api.kvassoedik.workers.dev/
curl https://edge-api.kvassoedik.workers.dev/health
curl https://edge-api.kvassoedik.workers.dev/edge
curl https://edge-api.kvassoedik.workers.dev/config
curl https://edge-api.kvassoedik.workers.dev/counter
```

Outputs:
```bash
curl https://edge-api.kvassoedik.workers.dev/
{"app":"edge-api","course":"devops-core","message":"Hello from Cloudflare Workers","routes":["/","/health","/edge","/config","/counter"],"timestamp":"2026-05-14T17:51:22.751Z"}(.venv) kapi@kapi-MDG-XX:~/Documents/Uni/S26/DevOps-Core-Course$ curl https://edge-api.kvassoedik.workers.dev/health
{"status":"ok","runtime":"cloudflare-workers","timestamp":"2026-05-14T17:51:28.431Z"}(.venv) kapi@kapi-MDG-XX:~/Documents/Uni/S26/DevOps-Core-Course$ curl https://edge-api.kvassoedik.workers.dev/edge
{"colo":"ARN","country":"FI","city":"Helsinki","asn":26383,"httpProtocol":"HTTP/2","tlsVersion":"TLSv1.3"}(.venv) kapi@kapi-MDG-XX:~/Documents/Uni/S26/DevOps-Core-Course$ curl https://edge-api.kvassoedik.workers.dev/config
{"appName":"edge-api","courseName":"devops-core","adminEmailConfigured":true,"apiTokenConfigured":true,"note":"Secret values are not returned."}(.venv) kapi@kapi-MDG-XX:~/Documents/Uni/S26/DevOps-Core-Course$ curl https://edge-api.kvassoedik.workers.dev/counter
{"visits":1,"persistedIn":"Workers KV"}(.venv) kapi@kapi-MDG-XX:~/Documents/Uni/S26/DevOps-Core-Course$ curl https://edge-api.kvassoedik.workers.dev/counter
{"visits":2,"persistedIn":"Workers KV"}
```

## Task 3 — Global Edge Behavior

### Edge Metadata Endpoint

The `/edge` route returns Cloudflare request metadata from the edge runtime.

#### Example Response

```json
{
  "colo":"ARN",
  "country":"FI",
  "city":"Helsinki",
  "asn":26383,
  "httpProtocol":"HTTP/2",
  "tlsVersion":"TLSv1.3"
}
```

### Global Distribution Explanation

Cloudflare Workers automatically distributes execution across Cloudflare’s global edge network.  
Unlike traditional VM or Kubernetes deployments, there is no need to manually select regions or create multiple replicas in different locations.

The Worker executes close to the user automatically based on Cloudflare routing. This significantly reduces latency and simplifies deployment.

### Routing Concepts

#### `workers.dev`

`workers.dev` provides an automatically generated public URL for Workers deployments.

Example:

```text
https://edge-api.kvassoedik.workers.dev
```

#### Routes

Routes attach a Worker to traffic for an existing Cloudflare-managed domain.

#### Custom Domains

Custom domains allow Workers to fully serve traffic for a specific domain or subdomain.

## Task 4 — Configuration, Secrets & Persistence

### Environment Variables

The Worker uses plaintext environment variables configured in `wrangler.jsonc`.

#### Configured Variables

```json
"vars": {
  "APP_NAME": "edge-api",
  "COURSE_NAME": "devops-core"
}
```

#### Purpose

- `APP_NAME` identifies the application
- `COURSE_NAME` identifies the course context

Plaintext variables are useful for non-sensitive configuration but should not store secrets because they are committed to source control.

### Secrets

Two secrets were configured using Wrangler.

#### Commands Used

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

#### Verification

The `/config` endpoint confirmed that secrets were loaded successfully:

```json
{
  "adminEmailConfigured": true,
  "apiTokenConfigured": true
}
```

The actual secret values are not exposed publicly.

### Workers KV Persistence

#### KV Namespace Creation

```bash
npx wrangler kv namespace create SETTINGS
```

#### KV Binding

```json
{
  "binding": "SETTINGS",
  "id": "e228f613d3cf4ee9a052efdc950f427c"
}
```

#### Persistent Counter

The `/counter` route stores visits inside Workers KV.

#### Requests

First request:

```json
{
  "visits":1
}
```

Second request:

```json
{
  "visits":2
}
```

Third request after redeployment:

```json
{
  "visits":3
}
```

This verified that data persisted across deployments.

## Task 5 — Observability & Operations

### Logs

The Worker uses `console.log()` for request logging.

#### Tail Command

```bash
npx wrangler tail
```

#### Log Output

```text
(log) request { path: '/edge', colo: 'PRG', country: 'CZ' }
```

### Deployment History

#### List Deployments

```bash
npx wrangler deployments list
```

Several deployment versions were visible in the deployment history.

#### Example Versions

```text
a792ed27-beed-4e56-9e70-3066885e627a
b1f75f32-f890-4056-a50a-55a3424aae4f
```

### Rollback

A rollback was successfully performed using:

```bash
npx wrangler rollback
```

#### Rollback Result

```text
SUCCESS Worker Version b1f75f32-f890-4056-a50a-55a3424aae4f has been deployed to 100% of traffic.
```

## Kubernetes vs Cloudflare Workers Comparison

| Aspect | Kubernetes | Cloudflare Workers |
|---|---|---|
| Setup complexity | High | Low |
| Deployment speed | Moderate | Very fast |
| Global distribution | Manual configuration | Automatic |
| Cost for small apps | Higher | Usually lower |
| Persistence model | Volumes, databases | KV, D1, Durable Objects |
| Infrastructure control | Full control | Limited |
| Runtime flexibility | Any container workload | Lightweight edge runtime |
| Best use case | Complex backend systems | Edge APIs and lightweight services |

## When to Use Each

### Kubernetes is Better For

- Large distributed systems
- Stateful applications
- Custom runtimes and containers
- Complex networking and orchestration
- Full infrastructure control

### Cloudflare Workers is Better For

- Edge APIs
- Lightweight HTTP services
- Global low-latency applications
- Serverless deployments
- Fast prototyping

## Reflection

### What Felt Easier Than Kubernetes

- Deployment workflow
- Global distribution
- Public HTTPS access
- Scaling and infrastructure management

### What Felt More Constrained

- Limited runtime environment
- No Docker containers
- Fewer low-level configuration options

### What Changed Because Workers Is Not a Docker Host

The application had to be written specifically for the Workers runtime instead of running inside a container.  
Traditional server concepts such as background services and custom operating system packages are not used in Workers.

## Conclusion

In this lab, a fully functional Cloudflare Workers API was developed and deployed globally using the Cloudflare edge platform.

The implementation included:

- Multiple HTTP endpoints
- Edge metadata inspection
- Environment variables
- Secret management
- Persistent storage using Workers KV
- Observability with logs
- Deployment versioning and rollback

The lab demonstrated the differences between traditional Kubernetes-based infrastructure and modern edge-based serverless computing.

---

P.S. VPN with two servers for traffic distribution is used, which causes two countries appear in outputs