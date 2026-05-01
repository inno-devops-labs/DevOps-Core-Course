interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
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
    const cf = request.cf;

    console.log("path=", url.pathname, "colo=", cf?.colo, "method=", request.method);

    if (url.pathname === "/health") {
      return Response.json({ status: "ok" });
    }

    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/meta") {
      return Response.json({
        app_name: env.APP_NAME,
        course: env.COURSE_NAME,
        worker_name: "edge-api",
        runtime: "cloudflare-workers",
        description: "Deployment metadata from plaintext vars (not secrets)",
      });
    }

    if (url.pathname === "/edge") {
      return Response.json({
        colo: cf?.colo,
        country: cf?.country,
        city: cf?.city,
        asn: cf?.asn,
        httpProtocol: cf?.httpProtocol,
        tlsVersion: cf?.tlsVersion,
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return Response.json({ visits, key: "visits", storage: "SETTINGS" });
    }

    if (url.pathname === "/admin") {
      const auth = request.headers.get("Authorization");
      const token = auth?.startsWith("Bearer ") ? auth.slice(7) : null;
      if (!token || token !== env.API_TOKEN) {
        return Response.json({ error: "unauthorized" }, { status: 401 });
      }
      return Response.json({
        message: "Authenticated using API_TOKEN (Wrangler secret)",
        admin_email: env.ADMIN_EMAIL,
      });
    }

    return new Response("Not Found", { status: 404 });
  },
};
