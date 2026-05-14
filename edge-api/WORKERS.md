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
