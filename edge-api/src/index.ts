export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

const START_TIME = Date.now();

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    console.log(`[${new Date().toISOString()}] ${request.method} ${url.pathname} from ${request.cf?.colo}`);

    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        description: "Edge API running on Cloudflare Workers (v2)",
        version: "2.0.0",
        uptime_ms: Date.now() - START_TIME,
        timestamp: new Date().toISOString(),
        endpoints: ["/", "/health", "/edge", "/counter"],
      });
    }

    if (url.pathname === "/health") {
      return Response.json({
        status: "healthy",
        timestamp: new Date().toISOString(),
        uptime_ms: Date.now() - START_TIME,
      });
    }

    if (url.pathname === "/edge") {
      return Response.json({
        colo: request.cf?.colo,
        country: request.cf?.country,
        city: request.cf?.city,
        asn: request.cf?.asn,
        httpProtocol: request.cf?.httpProtocol,
        tlsVersion: request.cf?.tlsVersion,
        note: "Served from Cloudflare global edge — no region selection needed",
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return Response.json({
        visits,
        stored_by: env.APP_NAME,
        persisted: true,
      });
    }

    return Response.json({ error: "Not Found", path: url.pathname }, { status: 404 });
  },
};
