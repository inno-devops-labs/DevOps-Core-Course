/**
 * Cloudflare Workers Edge API
 *
 * Routes:
 *   /         — General app information
 *   /health   — Health-check endpoint
 *   /edge     — Edge metadata (colo, country, city, asn, httpProtocol, tlsVersion)
 *   /counter  — KV-backed persistent visit counter
 */

export interface Env {
  /** Plaintext variable defined in wrangler.jsonc */
  APP_NAME: string;
  /** Plaintext variable defined in wrangler.jsonc */
  COURSE_NAME: string;
  /** Secret set via `npx wrangler secret put API_TOKEN` */
  API_TOKEN: string;
  /** Secret set via `npx wrangler secret put ADMIN_EMAIL` */
  ADMIN_EMAIL: string;
  /** KV namespace bound in wrangler.jsonc */
  SETTINGS: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Log every incoming request (visible via `npx wrangler tail`)
    console.log("request", url.pathname, "method", request.method, "colo", (request as any).cf?.colo);

    // ── Route: / ────────────────────────────────────────────────
    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers edge network",
        timestamp: new Date().toISOString(),
      });
    }

    // ── Route: /health ──────────────────────────────────────────
    if (url.pathname === "/health") {
      return Response.json({ status: "ok", timestamp: new Date().toISOString() });
    }

    // ── Route: /edge ────────────────────────────────────────────
    if (url.pathname === "/edge") {
      const cf = (request as any).cf;
      return Response.json({
        colo: cf?.colo,
        country: cf?.country,
        city: cf?.city,
        asn: cf?.asn,
        httpProtocol: cf?.httpProtocol,
        tlsVersion: cf?.tlsVersion,
      });
    }

    // ── Route: /counter ─────────────────────────────────────────
    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return Response.json({ visits });
    }

    // ── 404 fallback ────────────────────────────────────────────
    return new Response("Not Found", { status: 404 });
  },
};
