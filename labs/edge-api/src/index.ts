// src/index.ts
export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  COUNTERS: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    console.log(`[${new Date().toISOString()}] ${request.method} ${path} | colo: ${request.cf?.colo}`);

    if (path === "/") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
        workerUrl: "https://edge-api.<YOUR_SUBDOMAIN>.workers.dev", // replace
      });
    }

    if (path === "/health") {
      return Response.json({ status: "ok", uptime: "all good" });
    }

    if (path === "/edge") {
      return Response.json({
        edge: {
          colo: request.cf?.colo,
          country: request.cf?.country,
          city: request.cf?.city,
          asn: request.cf?.asn,
          httpProtocol: request.cf?.httpProtocol,
          tlsVersion: request.cf?.tlsVersion,
        },
        timestamp: new Date().toISOString(),
      });
    }

    if (path === "/counter") {
      const raw = await env.COUNTERS.get("visits") ?? "0";
      const visits = parseInt(raw, 10) + 1;
      await env.COUNTERS.put("visits", String(visits));
      return Response.json({ visits });
    }

    return new Response("Not Found", { status: 404 });
  },
};