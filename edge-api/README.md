# edge-api — Cloudflare Workers Edge API

> Lab 17: Cloudflare Workers Edge Deployment  
> DevOps Core Course — Exam Alternative (Part 1 of 2)

A serverless HTTP API deployed on Cloudflare's global edge network using Cloudflare Workers and Wrangler CLI.

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- A Cloudflare account ([sign up free](https://dash.cloudflare.com/sign-up))

### 1. Install dependencies

```bash
npm install
```

### 2. Authenticate with Cloudflare

```bash
npx wrangler login
npx wrangler whoami
```

### 3. Create KV namespace

```bash
npx wrangler kv namespace create SETTINGS
```

Copy the returned `id` value into `wrangler.jsonc` under `kv_namespaces[0].id`.

### 4. Set secrets

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

### 5. Configure local secrets (for `wrangler dev`)

```bash
cp .dev.vars.example .dev.vars
# Edit .dev.vars with real values — this file is gitignored
```

### 6. Run locally

```bash
npm run dev
# or: npx wrangler dev
```

Test at `http://localhost:8787`.

### 7. Deploy

```bash
npm run deploy
# or: npx wrangler deploy
```

---

## API Endpoints

| Route      | Description                                      |
|------------|--------------------------------------------------|
| `GET /`    | App info (name, version, course, timestamp)      |
| `GET /health` | Health check — `{ status: "ok" }`            |
| `GET /edge`   | Cloudflare edge metadata (colo, country, etc.)|
| `GET /counter`| KV-backed persistent visit counter           |
| `GET /config` | Non-secret configuration summary             |

## Operations

```bash
# Stream real-time logs
npm run tail

# View deployment history
npm run deployments

# Rollback to previous version
npm run rollback
```

## Documentation

See [WORKERS.md](./WORKERS.md) for:
- Full deployment evidence
- Kubernetes vs Workers comparison
- Reflection on edge computing trade-offs
