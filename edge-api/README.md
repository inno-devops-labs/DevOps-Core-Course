# Edge API - Cloudflare Workers

A serverless HTTP API deployed on Cloudflare's global edge network.

## Features

- **Health Check** - `/health` endpoint for monitoring
- **Edge Metadata** - `/edge` returns request info (colo, country, ASN, etc.)
- **Persistent Counter** - `/counter` using Workers KV storage
- **Configuration** - `/config` shows environment configuration status

## Quick Start

### Prerequisites

- Node.js 18+
- npm
- Cloudflare account

### Setup

```bash
# Install dependencies
npm install

# Authenticate with Cloudflare
npx wrangler login

# Create KV namespace (run once)
npx wrangler kv namespace create SETTINGS

# Update wrangler.jsonc with the namespace ID from previous step

# Add secrets
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

### Development

```bash
# Run locally
npm run dev
```

Test endpoints:
- http://localhost:8787/
- http://localhost:8787/health
- http://localhost:8787/edge
- http://localhost:8787/counter
- http://localhost:8787/config
- POST http://localhost:8787/counter/reset (requires Authorization header)

### Deployment

```bash
# Deploy to Cloudflare
npm run deploy
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | App information |
| GET | `/health` | Health check |
| GET | `/edge` | Edge request metadata |
| GET | `/counter` | KV-backed counter (increment) |
| POST | `/counter/reset` | Reset counter (requires auth) |
| GET | `/config` | Configuration status |

## Configuration

### Environment Variables

Set in `wrangler.jsonc`:
- `APP_NAME` - Application name
- `COURSE_NAME` - Course identifier

### Secrets

Set via CLI:
- `API_TOKEN` - API authentication token
- `ADMIN_EMAIL` - Admin contact email

### KV Namespace

- `SETTINGS` - Persistent key-value storage for counter

## Project Structure

```
edge-api/
├── src/
│   └── index.ts      # Worker source code
├── wrangler.jsonc    # Worker configuration
├── package.json      # Dependencies and scripts
├── tsconfig.json     # TypeScript configuration
├── WORKERS.md        # Lab documentation
└── README.md         # This file
```

## Resources

- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/)
- [Workers KV](https://developers.cloudflare.com/kv/)

## License

MIT
