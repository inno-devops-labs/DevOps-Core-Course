export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    console.log("path", url.pathname, "colo", (request as any).cf?.colo);

    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "DevOps Info Service running on Cloudflare Workers — v2",
        version: "2.0.0",
        timestamp: new Date().toISOString(),
        contact: env.ADMIN_EMAIL,
        routes: ["/", "/health", "/edge", "/counter", "/secret-check"],
      });
    }

    if (url.pathname === "/secret-check") {
      const auth = request.headers.get("X-API-Token");
      if (auth !== env.API_TOKEN) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        });
      }
      return Response.json({ authorized: true, user: env.ADMIN_EMAIL });
    }

    if (url.pathname === "/health") {
      return Response.json({
        status: "ok",
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/edge") {
      const cf = (request as any).cf ?? {};
      return Response.json({
        colo: cf.colo ?? null,
        country: cf.country ?? null,
        city: cf.city ?? null,
        asn: cf.asn ?? null,
        httpProtocol: cf.httpProtocol ?? null,
        tlsVersion: cf.tlsVersion ?? null,
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return Response.json({ visits });
    }

    return new Response(JSON.stringify({ error: "Not Found" }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });
  },
};
