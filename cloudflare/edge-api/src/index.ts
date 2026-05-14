export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN_DEMO?: string;
  ADMIN_EMAIL?: string;
  SETTINGS?: KVNamespace;
}

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const cf = request.cf;

    console.log("request", {
      path: url.pathname,
      method: request.method,
      colo: cf?.colo,
      country: cf?.country,
    });

    if (url.pathname === "/" && request.method === "GET") {
      return jsonResponse({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
        routes: ["/", "/health", "/edge", "/counter", "/info"],
      });
    }

    if (url.pathname === "/health" && request.method === "GET") {
      return jsonResponse({
        status: "ok",
        version: "0.2.0",
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/edge" && request.method === "GET") {
      return jsonResponse({
        colo: cf?.colo ?? null,
        country: cf?.country ?? null,
        city: cf?.city ?? null,
        region: cf?.region ?? null,
        asn: cf?.asn ?? null,
        asOrganization: cf?.asOrganization ?? null,
        httpProtocol: cf?.httpProtocol ?? null,
        tlsVersion: cf?.tlsVersion ?? null,
        timezone: cf?.timezone ?? null,
      });
    }

    if (url.pathname === "/counter" && request.method === "GET") {
      if (!env.SETTINGS) {
        return jsonResponse(
          { error: "KV namespace SETTINGS not bound" },
          503,
        );
      }
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      console.log("counter", { visits, colo: cf?.colo });
      return jsonResponse({ visits });
    }

    if (url.pathname === "/info" && request.method === "GET") {
      return jsonResponse({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        hasApiToken: Boolean(env.API_TOKEN_DEMO),
        hasAdminEmail: Boolean(env.ADMIN_EMAIL),
        adminEmailMasked: env.ADMIN_EMAIL
          ? env.ADMIN_EMAIL.replace(/(.).+(@.+)/, "$1***$2")
          : null,
        kvBound: Boolean(env.SETTINGS),
      });
    }

    return jsonResponse({ error: "Not Found", path: url.pathname }, 404);
  },
} satisfies ExportedHandler<Env>;
