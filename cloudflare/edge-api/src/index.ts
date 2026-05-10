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
  COUNTER_KV: KVNamespace;
}

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/") {
      return jsonResponse({
        app: env.APP_NAME,
        message: "Hello friend!",
        framework: "Cloudflare Workers",
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/health") {
      return jsonResponse({
        status: "healthy",
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/edge") {
      return jsonResponse({
        colo: request.cf?.colo,
        country: request.cf?.country,
        city: request.cf?.city,
		asn: request.cf?.asn,
		httpProtocol: request.cf?.httpProtocol,
        tlsVersion: request.cf?.tlsVersion,
        userAgent: request.headers.get("User-Agent"),
      });
    }

    if (url.pathname === "/counter") {
      const current = await env.COUNTER_KV.get("visits");

      let count = current ? parseInt(current) : 0;

      count += 1;

      await env.COUNTER_KV.put("visits", count.toString());

      return jsonResponse({
        visits: count,
      });
    }

    return jsonResponse(
      {
        error: "Not Found",
      },
      404
    );
  },
};