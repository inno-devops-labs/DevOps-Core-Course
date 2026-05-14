/**
 * Welcome to Cloudflare Workers!
 * 
 * This is a template for a TypeScript Worker that handles multiple routes.
 * 
 * @see https://developers.cloudflare.com/workers/
 */

export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN?: string;
  ADMIN_EMAIL?: string;
  SETTINGS?: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    
    // Log request for observability
    console.log(`[${new Date().toISOString()}] ${request.method} ${url.pathname} from ${request.cf?.colo || 'unknown'}`);

    // Health check endpoint
    if (url.pathname === "/health") {
      return Response.json({ 
        status: "ok",
        timestamp: new Date().toISOString()
      });
    }

    // Root endpoint - app info
    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
      });
    }

    // Edge metadata endpoint
    if (url.pathname === "/edge") {
      return Response.json({
        colo: request.cf?.colo,
        country: request.cf?.country,
        city: request.cf?.city,
        region: request.cf?.region,
        asn: request.cf?.asn,
        asOrganization: request.cf?.asOrganization,
        httpProtocol: request.cf?.httpProtocol,
        tlsVersion: request.cf?.tlsVersion,
        edgeRequestHost: request.headers.get("host"),
      });
    }

    // Counter endpoint with KV persistence (GET - increment)
    if (url.pathname === "/counter" && request.method === "GET") {
      if (!env.SETTINGS) {
        return Response.json({ error: "KV namespace not configured" }, { status: 500 });
      }
      
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      
      return Response.json({ 
        visits,
        message: "Counter incremented successfully"
      });
    }

    // Counter reset endpoint (POST - requires admin)
    if (url.pathname === "/counter/reset" && request.method === "POST") {
      if (!env.SETTINGS) {
        return Response.json({ error: "KV namespace not configured" }, { status: 500 });
      }
      
      // Simple admin check via secret
      const authHeader = request.headers.get("Authorization");
      if (!authHeader || !authHeader.startsWith("Bearer ")) {
        return Response.json({ error: "Authorization required" }, { status: 401 });
      }
      
      await env.SETTINGS.put("visits", "0");
      
      return Response.json({ 
        visits: 0,
        message: "Counter reset successfully"
      });
    }

    // Config endpoint - shows configuration (not secrets)
    if (url.pathname === "/config") {
      return Response.json({
        appName: env.APP_NAME,
        courseName: env.COURSE_NAME,
        hasApiToken: !!env.API_TOKEN,
        hasAdminEmail: !!env.ADMIN_EMAIL,
        hasKV: !!env.SETTINGS,
      });
    }

    // 404 for unknown routes
    return new Response("Not Found", { 
      status: 404,
      headers: { "Content-Type": "text/plain" }
    });
  },
};
