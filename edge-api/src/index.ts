export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    console.log("path", url.pathname, "colo", (request as any).cf?.colo);

    // Root - general app information
    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
      });
    }

    // Health check
    if (url.pathname === "/health") {
      return Response.json({ status: "ok", timestamp: new Date().toISOString() });
    }

    // Edge metadata
    if (url.pathname === "/edge") {
      const cf = (request as any).cf;
      return Response.json({
        colo: cf?.colo,
        country: cf?.country,
        city: cf?.city,
        asn: cf?.asn,
        httpProtocol: cf?.httpProtocol,
        tlsVersion: cf?.tlsVersion,
      });
    }

    // KV-backed counter
    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return Response.json({ visits });
    }

    // Config endpoint - shows env vars and secret presence (not values)
    if (url.pathname === "/config") {
      return Response.json({
        app_name: env.APP_NAME,
        course_name: env.COURSE_NAME,
        api_token_configured: !!env.API_TOKEN,
        admin_email_configured: !!env.ADMIN_EMAIL,
        kv_bound: !!env.SETTINGS,
      });
    }

    return new Response("Not Found", { status: 404 });
  },
};
