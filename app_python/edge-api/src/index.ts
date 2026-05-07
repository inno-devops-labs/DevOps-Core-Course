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
    const cf = request.cf as Record<string, unknown> | undefined;

    console.log("path", url.pathname, "colo", cf?.colo, "country", cf?.country);

    // GET /
    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        version: "2.0.0",
        message: "Hello from Cloudflare Workers edge!",
        timestamp: new Date().toISOString(),
        routes: ["/", "/health", "/edge", "/counter"],
      });
    }

    // GET /health
    if (url.pathname === "/health") {
      return Response.json({
        status: "healthy",
        timestamp: new Date().toISOString(),
        app: env.APP_NAME,
      });
    }

    // GET /edge — edge metadata from request.cf
    if (url.pathname === "/edge") {
      return Response.json({
        colo: cf?.colo ?? null,
        country: cf?.country ?? null,
        city: cf?.city ?? null,
        asn: cf?.asn ?? null,
        httpProtocol: cf?.httpProtocol ?? null,
        tlsVersion: cf?.tlsVersion ?? null,
        note: "Served from Cloudflare edge node closest to the requester",
      });
    }

    // GET /counter — KV-backed persistent counter
    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return Response.json({ visits });
    }

    return new Response(
      JSON.stringify({ error: "Not Found", path: url.pathname }),
      { status: 404, headers: { "Content-Type": "application/json" } }
    );
  },
};
