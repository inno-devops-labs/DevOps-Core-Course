/**
 * edge-api — Cloudflare Workers HTTP API
 * Lab 17: Cloudflare Workers Edge Deployment
 *
 * Routes:
 *   GET /          — app info (env vars)
 *   GET /health    — health check
 *   GET /edge      — Cloudflare request metadata (colo, country, city, asn, etc.)
 *   GET /counter   — KV-backed persistent visit counter
 *   GET /config    — non-secret configuration summary
 *   *              — 404 Not Found
 */

// ─── Environment interface ────────────────────────────────────────────────────
// Plaintext vars come from wrangler.jsonc [vars].
// Secrets are set via `npx wrangler secret put` and never committed to Git.
// KV namespace is bound in wrangler.jsonc [kv_namespaces].
export interface Env {
  // Plaintext vars (wrangler.jsonc)
  APP_NAME: string;
  COURSE_NAME: string;
  APP_VERSION: string;
  ENVIRONMENT: string;

  // Secrets (wrangler secret put)
  API_TOKEN: string;
  ADMIN_EMAIL: string;

  // KV namespace binding
  SETTINGS: KVNamespace;
}

// ─── Worker entry point ───────────────────────────────────────────────────────
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // Observability: log every incoming request with edge location
    console.log(
      JSON.stringify({
        event: "request",
        method: request.method,
        path: url.pathname,
        colo: request.cf?.colo ?? "local",
        country: request.cf?.country ?? "unknown",
        timestamp: new Date().toISOString(),
      })
    );

    // ── Route: GET / ──────────────────────────────────────────────────────────
    if (url.pathname === "/" && request.method === "GET") {
      return Response.json({
        app: env.APP_NAME,
        version: env.APP_VERSION,
        course: env.COURSE_NAME,
        environment: env.ENVIRONMENT,
        message: "Hello from Cloudflare Workers — Lab 17 (v2)",
        timestamp: new Date().toISOString(),
        routes: ["/", "/health", "/edge", "/counter", "/config"],
        worker_url: "https://edge-api.malov-2005.workers.dev",
      });
    }

    // ── Route: GET /health ────────────────────────────────────────────────────
    if (url.pathname === "/health" && request.method === "GET") {
      return Response.json(
        {
          status: "ok",
          app: env.APP_NAME,
          version: env.APP_VERSION,
          timestamp: new Date().toISOString(),
        },
        { status: 200 }
      );
    }

    // ── Route: GET /edge ──────────────────────────────────────────────────────
    // Returns Cloudflare-injected request metadata available at the edge.
    // cf object is populated only on the real Cloudflare network;
    // it will be undefined during `wrangler dev` local mode.
    if (url.pathname === "/edge" && request.method === "GET") {
      const cf = request.cf;
      return Response.json({
        colo: cf?.colo ?? null,           // IATA airport code of the edge data-center
        country: cf?.country ?? null,     // ISO 3166-1 alpha-2 country code
        city: cf?.city ?? null,           // City name
        region: cf?.region ?? null,       // Region / state
        asn: cf?.asn ?? null,             // Autonomous System Number of the client
        httpProtocol: cf?.httpProtocol ?? null,   // e.g. "HTTP/2"
        tlsVersion: cf?.tlsVersion ?? null,       // e.g. "TLSv1.3"
        clientTrustScore: cf?.clientTrustScore ?? null,
        note: cf
          ? "Metadata injected by Cloudflare edge"
          : "cf object is null — running in local dev mode",
      });
    }

    // ── Route: GET /counter ───────────────────────────────────────────────────
    // Demonstrates Workers KV persistence: increments a visit counter on every
    // request and stores it in the SETTINGS KV namespace.
    // The value persists across deploys and Worker restarts.
    if (url.pathname === "/counter" && request.method === "GET") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      // waitUntil ensures the KV write completes even after the response is sent
      ctx.waitUntil(env.SETTINGS.put("visits", String(visits)));
      return Response.json({
        visits,
        message: "Counter incremented and persisted in Workers KV",
        storage: "Workers KV — SETTINGS namespace",
      });
    }

    // ── Route: GET /config ────────────────────────────────────────────────────
    // Shows non-secret configuration. Secrets (API_TOKEN, ADMIN_EMAIL) are
    // intentionally masked — they are available in env but must not be exposed.
    if (url.pathname === "/config" && request.method === "GET") {
      return Response.json({
        APP_NAME: env.APP_NAME,
        COURSE_NAME: env.COURSE_NAME,
        APP_VERSION: env.APP_VERSION,
        ENVIRONMENT: env.ENVIRONMENT,
        // Secrets are present in env but we only confirm they are set, never expose values
        API_TOKEN_SET: Boolean(env.API_TOKEN),
        ADMIN_EMAIL_SET: Boolean(env.ADMIN_EMAIL),
        note: "Secret values are masked. Use `npx wrangler secret list` to see secret names.",
      });
    }

    // ── 404 fallback ──────────────────────────────────────────────────────────
    console.log(JSON.stringify({ event: "not_found", path: url.pathname }));
    return Response.json(
      {
        error: "Not Found",
        path: url.pathname,
        available_routes: ["/", "/health", "/edge", "/counter", "/config"],
      },
      { status: 404 }
    );
  },
} satisfies ExportedHandler<Env>;
