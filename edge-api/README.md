# edge-api (Cloudflare Workers)

This folder contains the Worker for Lab 17.

## Local dev

Install dependencies (you need a JS package manager in your environment):

```bash
cd edge-api
npm i
npx wrangler dev
```

## Routes

- `GET /` basic info + route list
- `GET /health` health check
- `GET /meta` deployment metadata (env + runtime)
- `GET /edge` Cloudflare request metadata (`request.cf`)
- `GET /counter` read KV counter
- `POST /counter` increment KV counter
- `GET /settings/:key` read KV key
- `PUT /settings/:key` write KV key (requires `Authorization: Bearer <API_TOKEN>`)

