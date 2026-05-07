/**
 * Lab 17 — Cloudflare Workers edge API (DevOps Core Course).
 */

export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  /** Set via `wrangler secret put API_TOKEN` — never commit. */
  API_TOKEN: string;
  /** Set via `wrangler secret put ADMIN_EMAIL` — never commit. */
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

export default {
  async fetch(
    request: Request,
    env: Env,
    _ctx: ExecutionContext
  ): Promise<Response> {
    const url = new URL(request.url);

    console.log("request", {
      path: url.pathname,
      colo: request.cf?.colo,
      country: request.cf?.country,
    });

    if (url.pathname === "/health") {
      return Response.json({ status: "ok" });
    }

    if (url.pathname === "/edge") {
      return Response.json({
        colo: request.cf?.colo ?? null,
        country: request.cf?.country ?? null,
        city: request.cf?.city ?? null,
        asn: request.cf?.asn ?? null,
        httpProtocol: request.cf?.httpProtocol ?? null,
        tlsVersion: request.cf?.tlsVersion ?? null,
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return Response.json({ visits, persisted_in: "KV:SETTINGS" });
    }

    if (url.pathname === "/") {
      return Response.json({
        runtime: "cloudflare-workers",
        app_name: env.APP_NAME,
        course: env.COURSE_NAME,
        timestamp: new Date().toISOString(),
        routes: ["/", "/health", "/edge", "/counter"],
        secrets_configured: {
          api_token: Boolean(env.API_TOKEN),
          admin_email: Boolean(env.ADMIN_EMAIL),
        },
      });
    }

    return Response.json(
      { error: "Not Found", path: url.pathname },
      { status: 404 }
    );
  },
};
