export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  ENVIRONMENT: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

const VERSION = "1.0.0";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const cf = request.cf;

    console.log(
      "request",
      JSON.stringify({
        path: url.pathname,
        method: request.method,
        colo: cf?.colo,
        country: cf?.country,
      }),
    );

    if (url.pathname === "/" || url.pathname === "") {
      return jsonResponse({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        version: VERSION,
        framework: "cloudflare-workers",
        environment: env.ENVIRONMENT,
        timestamp: new Date().toISOString(),
        endpoints: ["/", "/health", "/edge", "/counter", "/config"],
      });
    }

    if (url.pathname === "/health") {
      return jsonResponse({
        status: "ok",
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/edge") {
      return jsonResponse({
        colo: cf?.colo ?? null,
        country: cf?.country ?? null,
        city: cf?.city ?? null,
        asn: cf?.asn ?? null,
        httpProtocol: cf?.httpProtocol ?? null,
        tlsVersion: cf?.tlsVersion ?? null,
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return jsonResponse({
        key: "visits",
        visits,
        stored_at: new Date().toISOString(),
      });
    }

    if (url.pathname === "/config") {
      return jsonResponse({
        app_name: env.APP_NAME,
        course_name: env.COURSE_NAME,
        environment: env.ENVIRONMENT,
        api_token_set: Boolean(env.API_TOKEN),
        admin_email_set: Boolean(env.ADMIN_EMAIL),
        kv_bound: typeof env.SETTINGS?.get === "function",
      });
    }

    return jsonResponse({ error: "not found", path: url.pathname }, 404);
  },
} satisfies ExportedHandler<Env>;
