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

  SETTINGS: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return Response.json({ status: "ok" });
    }

    if (url.pathname === "/edge") {
      return Edge(request);
    }
	
    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
	  const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return Response.json({
        visits
      });
    }

    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
      });
    }

    return new Response("Not Found", { status: 404 });
  },
};

async function Edge(request: Request): Promise<Response> {
	const cf = request.cf;
	return Response.json({ 
		colo: cf?.colo,
		country: cf?.country,
		region: cf?.region,
		city: cf?.city,
		timezone: cf?.timezone,
		latitude: cf?.latitude,
		longitude: cf?.longitude,
		edgeRequestKeepAliveStatus: cf?.edgeRequestKeepAliveStatus,
		httpProtocol: cf?.httpProtocol,
		requestPriority: cf?.requestPriority,
		tlsVersion: cf?.tlsVersion
	 });
}