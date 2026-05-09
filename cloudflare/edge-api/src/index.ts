export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

const json = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    console.log("request", request.method, path, "colo", request.cf?.colo, "country", request.cf?.country);

    if (request.method !== "GET") {
      return json({ error: "method not allowed" }, 405);
    }

    if (path === "/" || path === "") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        version: "v2",
        message: "Hello from Cloudflare Workers",
        routes: ["/", "/health", "/edge", "/config", "/counter"],
        timestamp: new Date().toISOString(),
      });
    }

    if (path === "/health") {
      return json({ status: "ok", app: env.APP_NAME });
    }

    if (path === "/edge") {
      const cf = request.cf ?? {};
      return json({
        colo: cf.colo,
        country: cf.country,
        city: cf.city,
        region: cf.region,
        asn: cf.asn,
        asOrganization: cf.asOrganization,
        httpProtocol: cf.httpProtocol,
        tlsVersion: cf.tlsVersion,
        timezone: cf.timezone,
      });
    }

    if (path === "/config") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        secretsConfigured: {
          apiToken: Boolean(env.API_TOKEN),
          adminEmail: Boolean(env.ADMIN_EMAIL),
        },
      });
    }

    if (path === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return json({ visits, key: "visits" });
    }

    return json({ error: "not found", path }, 404);
  },
} satisfies ExportedHandler<Env>;
