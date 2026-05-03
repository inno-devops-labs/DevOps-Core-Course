/**
 * Welcome to Cloudflare Workers! This is your first worker.
 *
 * - Run `npm run dev` in your terminal to start a development server
 * - Open a browser tab at http://localhost:8787/ to see your worker in action
 * - Run `npm run deploy` to publish your worker
 *
 * Bind resources to your worker in `wrangler.jsonc`. After adding bindings, a type definition for the
 * `Env` object can be regenerated with `npm run cf-typegen`.
 *
 * Learn more at https://developers.cloudflare.com/workers/
 */

export interface Env {
  APP_NAME: string;
  APP_VERSION: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const method = request.method;

    console.log(`[${method}] ${url.pathname} - ${request.cf?.colo || 'unknown'}`);

    // GET /health
    if (url.pathname === "/health" && method === "GET") {
      return Response.json({
        status: "ok",
        timestamp: new Date().toISOString(),
        version: env.APP_VERSION,
      });
    }

    // GET / app data
    if (url.pathname === "/" && method === "GET") {
      return Response.json({
        app: env.APP_NAME,
        version: env.APP_VERSION,
        message: "Hello from Cloudflare Workers!",
        timestamp: new Date().toISOString(),
        endpoints: [
          "GET / - Application info",
          "GET /health - Health check",
          "GET /edge - Edge metadata (colo, country, etc.)",
          "GET /counter - Persistent counter (KV)",
          "POST /counter - Increment counter",
        ],
      });
    }

    // GET /edge — edge metadata
    if (url.pathname === "/edge" && method === "GET") {
      return Response.json({
        colo: request.cf?.colo || "unknown",
        country: request.cf?.country || "unknown",
        city: request.cf?.city || "unknown",
        continent: request.cf?.continent || "unknown",
        asn: request.cf?.asn || "unknown",
        asOrganization: request.cf?.asOrganization || "unknown",
        httpProtocol: request.cf?.httpProtocol || "unknown",
        tlsVersion: request.cf?.tlsVersion || "unknown",
        timezone: request.cf?.timezone || "unknown",
        timestamp: new Date().toISOString(),
      });
    }

    // GET /counter — get visit counter
    if (url.pathname === "/counter" && method === "GET") {
      const visits = await env.SETTINGS.get("visits");
      const count = Number(visits ?? "0");
      return Response.json({
        visits: count,
        message: "Call POST /counter to increment",
      });
    }

    // POST /counter — increase counter
    if (url.pathname === "/counter" && method === "POST") {
      const current = await env.SETTINGS.get("visits");
      const newCount = Number(current ?? "0") + 1;
      await env.SETTINGS.put("visits", String(newCount));
	  const verify = await env.SETTINGS.get("visits");
      return Response.json({
        visits: newCount,
        message: "Counter incremented successfully",
		verification: verify,
      });
    }

    // 404 Not Found
    return new Response(
      JSON.stringify({
        error: "Not Found",
        path: url.pathname,
        method: method,
      }),
      {
        status: 404,
        headers: { "Content-Type": "application/json" },
      }
    );
  },
};
