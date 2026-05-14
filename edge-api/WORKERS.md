# Lab 17 Workers Notes

## Task 3 - Global Edge Behavior

Worker URL: `https://edge-api.neilzvest.workers.dev`

The Worker exposes `/edge` to return Cloudflare request metadata from the incoming request context. The endpoint includes the required `colo` and `country` fields plus additional fields: `city`, `asn`, `httpProtocol`, and `tlsVersion`.

Public verification captured on 2026-05-14:

```bash
curl -sS -w "\nHTTP %{http_code}\n" https://edge-api.neilzvest.workers.dev/edge
```

```json
{
  "app": "edge-api",
  "colo": "FRA",
  "country": "DE",
  "city": "Frankfurt am Main",
  "asn": 213877,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3",
  "timestamp": "2026-05-14T13:02:35.891Z"
}
```

HTTP status:

```text
HTTP 200
```

This response shows that Cloudflare executed the Worker on its edge network and attached request metadata to `request.cf`. In this request, Cloudflare handled the request through the `FRA` colo and provided network/protocol details such as ASN, HTTP protocol, and TLS version.

### Global Distribution

Cloudflare Workers are deployed to Cloudflare's global edge network. A single deployment makes the Worker available globally, and Cloudflare routes each incoming request to an appropriate nearby data center. The application code does not need region-specific replicas.

This is different from VM, Kubernetes, or many PaaS deployments where you usually choose one or more regions manually, deploy infrastructure into each region, configure load balancing, and manage regional capacity. With Workers, Cloudflare owns the regional placement and routing layer.

There is no separate "deploy to 3 regions" step because `wrangler deploy` publishes the Worker to Cloudflare's edge platform as a globally available service. Global request routing is part of the platform behavior.

### Routing Concepts

`workers.dev` is Cloudflare's default public URL for Workers. It is useful for this lab because it gives the Worker a reachable HTTPS URL without buying or configuring a custom domain.

Routes attach a Worker to matching traffic for an existing Cloudflare zone. For example, a route can make a Worker handle selected paths under a domain already managed by Cloudflare.

Custom Domains bind a Worker directly to a domain or subdomain so the Worker can serve traffic from that hostname. This lab uses `workers.dev`; custom domains are optional.

References:

- Cloudflare Workers Overview: https://developers.cloudflare.com/workers/
- Request API and `request.cf`: https://developers.cloudflare.com/workers/runtime-apis/request/
- `workers.dev` routing: https://developers.cloudflare.com/workers/configuration/routing/workers-dev/
- Routes and domains: https://developers.cloudflare.com/workers/configuration/routing/

## Task 4 - Configuration, Secrets, and Persistence

Plaintext variables are configured in `wrangler.jsonc`:

```json
{
  "vars": {
    "APP_NAME": "edge-api",
    "COURSE_NAME": "devops-core"
  }
}
```

The Worker uses these values through `env.APP_NAME` and `env.COURSE_NAME` in `/`, `/health`, `/metadata`, and `/config`.

Plaintext vars are not suitable for secrets because they are committed to source control in `wrangler.jsonc`. They are appropriate for non-sensitive configuration such as app names, feature flags, or course labels. Secret values should be stored with Wrangler secrets because Cloudflare stores them outside the repository and injects them into the Worker environment at runtime.

Two secrets were configured with Wrangler:

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

The Worker reads these through `env.API_TOKEN` and `env.ADMIN_EMAIL`, but it does not return the raw secret values. `/config` only returns whether each secret is configured and the email domain:

```json
{
  "app": "edge-api",
  "course": "devops-core",
  "plaintextVars": ["APP_NAME", "COURSE_NAME"],
  "secrets": {
    "apiTokenConfigured": true,
    "adminEmailConfigured": true,
    "adminEmailDomain": "gmail.com"
  },
  "note": "Secret values are read from env but are not returned."
}
```

Workers KV persistence is configured with a namespace bound as `SETTINGS`:

```json
{
  "kv_namespaces": [
    {
      "binding": "SETTINGS",
      "id": "f4c891b632f746e791d55f1a6fe80c1f"
    }
  ]
}
```

The `/counter` endpoint reads the `visits` key from `env.SETTINGS`, increments it, writes it back, and returns the new value.

Persistence verification:

```bash
curl -sS -w "\nHTTP %{http_code}\n" https://edge-api.neilzvest.workers.dev/counter
```

Before redeploy:

```json
{
  "key": "visits",
  "visits": 1,
  "persistedIn": "Workers KV"
}
```

After redeploy:

```json
{
  "key": "visits",
  "visits": 2,
  "persistedIn": "Workers KV"
}
```

The value increased after redeploy, which confirms the counter state is stored in Workers KV rather than in Worker memory.
