export interface Env {
  APP_NAME: string;      // plaintext var
  API_TOKEN: string;     // secret
  ADMIN_EMAIL: string;   // secret
  SETTINGS: KVNamespace; // KV binding
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // Log for observability (Task 5)
    console.log(`[${new Date().toISOString()}] ${request.method} ${path}`);

    // GET /health
    if (path === "/health") {
      return Response.json({ status: "ok", timestamp: new Date().toISOString() });
    }

    // GET / (main information)
    if (path === "/") {
      return Response.json({
        app: env.APP_NAME,
        message: "Hello from Cloudflare Workers edge API",
        version: "1.0.0",
        endpoints: ["/", "/health", "/edge", "/counter", "/admin"],
      });
    }

    // GET /edge – edge metadata (Task 3)
    if (path === "/edge") {
      const cf = request.cf;
      return Response.json({
        colo: cf?.colo ?? "unknown",
        country: cf?.country ?? "unknown",
        city: cf?.city ?? "unknown",
        asn: cf?.asn ?? "unknown",
        httpProtocol: cf?.httpProtocol ?? "unknown",
        tlsVersion: cf?.tlsVersion ?? "unknown",
      });
    }

    // GET /counter – KV-backed counter (Task 4)
    if (path === "/counter") {
      let visits = Number(await env.SETTINGS.get("visits")) || 0;
      visits++;
      await env.SETTINGS.put("visits", String(visits));
      return Response.json({ visits, pod: "edge-worker" });
    }

    // GET /admin – requires API token secret
    if (path === "/admin") {
      const authHeader = request.headers.get("Authorization");
      const token = authHeader?.replace("Bearer ", "");
      if (token !== env.API_TOKEN) {
        return new Response("Unauthorized", { status: 401 });
      }
      return Response.json({
        adminEmail: env.ADMIN_EMAIL,
        message: "Admin area",
      });
    }

    return new Response("Not Found", { status: 404 });
  },
};