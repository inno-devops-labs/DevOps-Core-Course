export interface Env {
  // Task 4: plaintext vars (defined in wrangler.jsonc)
  APP_NAME: string;
  COURSE_NAME: string;

  // Task 4: secrets (set via `wrangler secret put`)
  API_TOKEN: string;
  ADMIN_EMAIL: string;

  // Task 4: KV namespace binding
  SETTINGS: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Task 5: log every incoming request for observability
    console.log(
      JSON.stringify({
        event: "request",
        path: url.pathname,
        method: request.method,
        colo: request.cf?.colo ?? "unknown",
        country: request.cf?.country ?? "unknown",
        ts: new Date().toISOString(),
      })
    );

    // ── CORS helper ──────────────────────────────────────────────────────────
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Content-Type": "application/json",
    };

    // ── Route: GET / ─────────────────────────────────────────────────────────
    if (url.pathname === "/" && request.method === "GET") {
      return Response.json(
        {
          app: env.APP_NAME,
          course: env.COURSE_NAME,
          message: "Hello from Cloudflare Workers 🌍 — v2",
          timestamp: new Date().toISOString(),
          routes: ["/", "/health", "/edge", "/counter", "/config"],
        },
        { headers: corsHeaders }
      );
    }

    // ── Route: GET /health ───────────────────────────────────────────────────
    if (url.pathname === "/health" && request.method === "GET") {
      return Response.json(
        {
          status: "ok",
          app: env.APP_NAME,
          timestamp: new Date().toISOString(),
        },
        { headers: corsHeaders }
      );
    }

    // ── Route: GET /edge  (Task 3) ───────────────────────────────────────────
    // Returns Cloudflare request metadata — proves edge-side execution
    if (url.pathname === "/edge" && request.method === "GET") {
      return Response.json(
        {
          colo: request.cf?.colo,          // IATA airport code of the PoP
          country: request.cf?.country,    // ISO 3166-1 alpha-2 country
          city: request.cf?.city,          // city of the visitor
          asn: request.cf?.asn,            // autonomous system number
          httpProtocol: request.cf?.httpProtocol,  // HTTP/1.1, HTTP/2, HTTP/3
          tlsVersion: request.cf?.tlsVersion,
          requestPriority: request.cf?.requestPriority,
          note: "This data is injected by Cloudflare at the edge PoP closest to the caller.",
        },
        { headers: corsHeaders }
      );
    }

    // ── Route: GET /counter  (Task 4 — KV persistence) ──────────────────────
    if (url.pathname === "/counter" && request.method === "GET") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));

      console.log(JSON.stringify({ event: "counter", visits }));

      return Response.json(
        {
          visits,
          note: "Persisted in Workers KV — survives redeploys.",
        },
        { headers: corsHeaders }
      );
    }

    // ── Route: GET /config  (Task 4 — env vars + secrets presence check) ────
    if (url.pathname === "/config" && request.method === "GET") {
      return Response.json(
        {
          APP_NAME: env.APP_NAME,
          COURSE_NAME: env.COURSE_NAME,
          // Never expose secret values — only confirm they are set
          API_TOKEN_set: Boolean(env.API_TOKEN),
          ADMIN_EMAIL_set: Boolean(env.ADMIN_EMAIL),
          note: "Secret values are never exposed; only their presence is shown.",
        },
        { headers: corsHeaders }
      );
    }

    // ── 404 fallback ─────────────────────────────────────────────────────────
    console.log(JSON.stringify({ event: "not_found", path: url.pathname }));
    return new Response(
      JSON.stringify({ error: "Not Found", path: url.pathname }),
      { status: 404, headers: corsHeaders }
    );
  },
};