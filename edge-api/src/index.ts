export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function getClientIp(request: Request): string {
  return request.headers.get("CF-Connecting-IP") ?? "unknown";
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Required for observability task
    console.log("request", {
      path: url.pathname,
      method: request.method,
      colo: request.cf?.colo,
      country: request.cf?.country,
    });

    if (url.pathname === "/health" && request.method === "GET") {
      return json({
        status: "ok",
        service: env.APP_NAME,
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/" && request.method === "GET") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
        endpoints: ["/", "/health", "/edge", "/config", "/counter", "/counter/reset"],
      });
    }

    if (url.pathname === "/edge" && request.method === "GET") {
      return json({
        colo: request.cf?.colo,
        country: request.cf?.country,
        city: request.cf?.city,
        asn: request.cf?.asn,
        httpProtocol: request.cf?.httpProtocol,
        tlsVersion: request.cf?.tlsVersion,
        clientIp: getClientIp(request),
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/config" && request.method === "GET") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        secret_presence: {
          api_token_set: Boolean(env.API_TOKEN),
          admin_email_set: Boolean(env.ADMIN_EMAIL),
        },
      });
    }

    if (url.pathname === "/counter" && request.method === "GET") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return json({ visits, source: "workers-kv" });
    }

    if (url.pathname === "/counter/reset" && request.method === "POST") {
      await env.SETTINGS.put("visits", "0");
      return json({ reset: true, visits: 0 });
    }

    return json(
      {
        error: "Not Found",
        path: url.pathname,
      },
      404,
    );
  },
};
