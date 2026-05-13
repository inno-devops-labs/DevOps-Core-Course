interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  APP_ENV: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

interface EdgeInfo {
  colo?: string;
  country?: string;
  city?: string;
  asn?: number;
  region?: string;
  continent?: string;
  httpProtocol?: string;
  tlsVersion?: string;
}

function json(data: unknown, init?: ResponseInit): Response {
  return new Response(JSON.stringify(data, null, 2), {
    ...init,
    headers: {
      "content-type": "application/json; charset=utf-8",
      ...(init?.headers ?? {})
    }
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method.toUpperCase();
    const now = new Date().toISOString();

    const cf = (request as Request & { cf?: EdgeInfo }).cf;
    console.log("request", {
      path,
      method,
      colo: cf?.colo,
      country: cf?.country,
      protocol: cf?.httpProtocol
    });

    if (method === "GET" && path === "/health") {
      return json({
        status: "ok",
        app: env.APP_NAME,
        env: env.APP_ENV,
        timestamp: now
      });
    }

    if (method === "GET" && path === "/") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        env: env.APP_ENV,
        message: "Hello from Cloudflare Workers",
        timestamp: now,
        routes: ["/", "/health", "/edge", "/counter", "/config"]
      });
    }

    if (method === "GET" && path === "/edge") {
      return json({
        timestamp: now,
        edge: {
          colo: cf?.colo ?? null,
          country: cf?.country ?? null,
          city: cf?.city ?? null,
          asn: cf?.asn ?? null,
          region: cf?.region ?? null,
          continent: cf?.continent ?? null,
          httpProtocol: cf?.httpProtocol ?? null,
          tlsVersion: cf?.tlsVersion ?? null
        }
      });
    }

    if (method === "GET" && path === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));

      return json({
        visits,
        kvKey: "visits",
        persisted: true,
        timestamp: now
      });
    }

    if (method === "GET" && path === "/config") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        env: env.APP_ENV,
        adminEmailConfigured: Boolean(env.ADMIN_EMAIL),
        apiTokenConfigured: Boolean(env.API_TOKEN),
        note: "Secret values are intentionally not returned"
      });
    }

    return json(
      {
        error: "Not Found",
        path,
        method
      },
      { status: 404 }
    );
  }
};
