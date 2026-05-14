/**
 * Lab 17 — Cloudflare Workers edge API (TypeScript).
 * Routes: /health, /, /meta, /edge, /counter
 */

export interface Env {
  /** Plaintext var from wrangler.jsonc */
  APP_NAME: string;
  COURSE_NAME: string;
  /** Secrets — set with `npx wrangler secret put ...` (use .dev.vars locally) */
  API_TOKEN?: string;
  ADMIN_EMAIL?: string;
  SETTINGS: KVNamespace;
}

const VISITS_KEY = "visits";

function json(data: unknown, init?: ResponseInit): Response {
  return Response.json(data, {
    ...init,
    headers: { "content-type": "application/json; charset=utf-8", ...init?.headers },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const cf = request.cf;

    console.log("request", { path: url.pathname, colo: cf?.colo, method: request.method });

    if (url.pathname === "/health") {
      return json({
        status: "healthy",
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/") {
      return json({
        service: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
        endpoints: ["/health", "/", "/meta", "/edge", "/counter"],
      });
    }

    if (url.pathname === "/meta") {
      return json({
        worker: env.APP_NAME,
        course: env.COURSE_NAME,
        runtime: "cloudflare-workers",
        timestamp: new Date().toISOString(),
        bindings: {
          plaintextVars: ["APP_NAME", "COURSE_NAME"],
          secretsPresent: {
            API_TOKEN: Boolean(env.API_TOKEN),
            ADMIN_EMAIL: Boolean(env.ADMIN_EMAIL),
          },
          kv: { binding: "SETTINGS", configured: Boolean(env.SETTINGS) },
        },
        note: "Plaintext vars are visible in the dashboard and in wrangler config; never put secrets there.",
      });
    }

    if (url.pathname === "/edge") {
      return json({
        colo: cf?.colo ?? null,
        country: cf?.country ?? null,
        city: cf?.city ?? null,
        asn: cf?.asn ?? null,
        httpProtocol: cf?.httpProtocol ?? null,
        tlsVersion: cf?.tlsVersion ?? null,
        region: cf?.region ?? null,
        timezone: cf?.timezone ?? null,
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get(VISITS_KEY);
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put(VISITS_KEY, String(visits));
      return json({ visits, key: VISITS_KEY });
    }

    return new Response(
      JSON.stringify({
        error: "Not Found",
        path: url.pathname,
        hint: "Try /, /health, /meta, /edge, /counter",
      }),
      { status: 404, headers: { "content-type": "application/json; charset=utf-8" } },
    );
  },
};
